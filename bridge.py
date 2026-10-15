"""Read-only PM5 bridge. One BLE connection serves bar and localhost browser."""
import asyncio
import json
import os
from pathlib import Path
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

ADDRESS = 'FE:B5:DD:E6:C6:F8'
ROOT = Path(__file__).parent
STATUS = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'bikeerg.json'
state = {'connected': False, 'status': 'Söker PM5', 'device': 'PM5 431575390', 'metrics': {}, 'raw': {}}
lock = threading.Lock()

def publish(**changes):
    with lock:
        state.update(changes)
        state['updated'] = time.time()
        payload = json.dumps(state, ensure_ascii=False)
    tmp = STATUS.with_suffix('.tmp')
    tmp.write_text(payload)
    tmp.replace(STATUS)

def indoor(data):
    flags = int.from_bytes(data[:2], 'little')
    offset = 2
    values = {}
    def take(n, signed=False, scale=1):
        nonlocal offset
        if offset+n > len(data):
            raise ValueError('Short FTMS packet')
        v = int.from_bytes(data[offset:offset+n], 'little', signed=signed)*scale
        offset += n
        return v
    if not flags & 1: values['speed_kmh'] = take(2, scale=.01)
    for bit, key, n, signed, scale in [
        (1,'average_speed_kmh',2,False,.01), (2,'cadence_rpm',2,False,.5),
        (3,'average_cadence_rpm',2,False,.5), (4,'distance_m',3,False,1),
        (5,'resistance',2,True,1), (6,'power_w',2,True,1),
        (7,'average_power_w',2,True,1)]:
        if flags & (1<<bit): values[key] = take(n,signed,scale)
    if flags & (1<<8):
        values.update(calories_kcal=take(2), calories_per_hour=take(2), calories_per_minute=take(1))
    for bit,key,n,scale in [(9,'heart_rate_bpm',1,1),(10,'metabolic_equivalent',1,.1),(11,'elapsed_s',2,1),(12,'remaining_s',2,1)]:
        if flags & (1<<bit): values[key] = take(n,scale=scale)
    return values

def notify(kind):
    def received(_, data):
        try:
            if kind == 'indoor_bike': values = indoor(data)
            elif kind == 'power': values = {'power_w': struct.unpack_from('<h',data,2)[0]}
            else: values = {}
            with lock:
                state['metrics'].update(values)
                state['raw'][kind] = {'hex': data.hex(), 'timestamp': time.time()}
                state['last_sample'] = time.time()
            publish()
        except (ValueError,struct.error): pass
    return received

async def ride():
    while True:
        try:
            publish(connected=False,status='Ansluter till PM5')
            # Use BlueZ's existing object when available; scanning an already
            # connected PM5 may fail because it no longer advertises.
            from dbus_fast.aio import MessageBus
            from dbus_fast import BusType, Message
            bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
            try:
                reply = await bus.call(Message(destination='org.bluez',path='/',interface='org.freedesktop.DBus.ObjectManager',member='GetManagedObjects'))
                objects = reply.body[0]
                path = next((p for p, interfaces in objects.items() if 'org.bluez.Device1' in interfaces and interfaces['org.bluez.Device1'].get('Address') and interfaces['org.bluez.Device1']['Address'].value == ADDRESS),None)
            finally: bus.disconnect()
            device = BLEDevice(ADDRESS,'PM5',{'path':path}) if path else await BleakScanner.find_device_by_address(ADDRESS,timeout=10)
            if not device: raise RuntimeError('PM5 hittas inte – välj Connect på monitorn')
            async with BleakClient(device,timeout=15) as client:
                subscribed=[]
                for uuid,kind in [('00002ad2-0000-1000-8000-00805f9b34fb','indoor_bike'),('00002a63-0000-1000-8000-00805f9b34fb','power')]:
                    if client.services.get_characteristic(uuid):
                        await client.start_notify(uuid,notify(kind)); subscribed.append(kind)
                if not subscribed: raise RuntimeError('Inga träningsdata tillgängliga')
                publish(connected=True,status='Ansluten',subscriptions=subscribed)
                while client.is_connected:
                    publish()
                    await asyncio.sleep(1)
        except Exception as exc:
            publish(connected=False,status=str(exc),metrics={},last_sample=0)
            await asyncio.sleep(5)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get('Host') not in ('127.0.0.1:18765','localhost:18765'):
            self.send_error(403); return
        if self.path == '/api/state':
            with lock: body=json.dumps(state,ensure_ascii=False).encode()
            mime='application/json'
        elif self.path in ('/','/game'):
            body=(ROOT/'game.html').read_bytes(); mime='text/html; charset=utf-8'
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type',mime)
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass

if __name__ == '__main__':
    server=ThreadingHTTPServer(('127.0.0.1',18765),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    asyncio.run(ride())
