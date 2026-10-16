from playwright.sync_api import sync_playwright,expect
import time
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 live={'connected':False,'metrics':{}}
 def respond(route):
  route.fulfill(json={**live,'last_sample':time.time()})
 page.route('**/api/state',respond)
 page.goto('http://127.0.0.1:18765/game')
 page.get_by_role('button',name='Orbital',exact=False).click()
 page.get_by_role('button',name='Starta uppdrag').click()
 expect(page.locator('#overtitle')).to_have_text('Börja trampa')
 live.update(connected=True,metrics={'power_w':0})
 page.wait_for_timeout(700)
 expect(page.locator('#overlay')).to_be_visible()
 assert page.evaluate('gameTime')==0
 assert page.evaluate('shots.length')==0
 live['metrics']['power_w']=1
 expect(page.locator('#overlay')).to_be_hidden()
 page.wait_for_function('shots.length>0')
 # Ramp from minimal power to target; must not wait out the former 5s cooldown.
 page.evaluate('shots=[];shotClock=0')
 live['metrics']['power_w']=100
 page.wait_for_function('shots.length>=2',timeout=1500)
 live['metrics']['power_w']=0
 expect(page.locator('#watts')).to_have_text('0')
 page.wait_for_timeout(1500)
 assert page.evaluate('shots.length')==0
 live['metrics']['power_w']=100
 page.wait_for_function('shots.length>0',timeout=1000)
 assert page.evaluate('energy')<100
 page.get_by_role('button',name='Spelmeny',exact=True).click()
 page.get_by_role('button',name='Prova demo utan cykel').click()
 page.locator('#demowatts').fill('100')
 page.wait_for_function('energy>=100',timeout=11000)
 expect(page.locator('#hudenergytext')).to_have_text('REDO')
 assert page.locator('#hudenergy').evaluate('(e)=>e.value')==100
 page.keyboard.press('Space')
 page.wait_for_function('energy<1',timeout=2000)
 assert page.evaluate('boostRemaining>9 && enemies.length>0')
 assert not errors,errors
 print('Live-data autofire checks passed: zero-watt wait, first pedal, ramp-up, stop and restart; no Space presses.')
 b.close()
