"""Responsive arcade and one full kart lap using actual keyboard events."""
import math
import time
from playwright.sync_api import sync_playwright, expect


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':390,'height':844})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:18765/game')
    expect(page.locator('.stage')).to_be_hidden()
    expect(page.locator('#powerhud')).to_be_hidden()
    expect(page.locator('.gamecard')).to_have_count(3)
    overlay = page.locator('#overlay').bounding_box()
    last_card = page.locator('.gamecard').last.bounding_box()
    assert last_card['y']+last_card['height'] <= overlay['y']+overlay['height']
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')

    page.get_by_role('button', name='Orbital', exact=False).click()
    stage = page.locator('.stage').bounding_box()
    assert abs(stage['width']/stage['height']-1000/690)<.01
    watts = page.locator('#target')
    watts.focus()
    watts.press('ArrowUp')
    expect(watts).to_have_value('105')

    page.set_viewport_size({'width':1440,'height':1000})
    page.get_by_role('button', name='Arkaden', exact=True).click()
    page.get_by_role('button', name='Velodrift', exact=False).click()
    page.get_by_role('button', name='Prova demo utan cykel').click()
    page.locator('#demowatts').fill('105')
    assert page.evaluate('kartOnRoad(500,180) && !kartOnRoad(900,345)')
    held = None
    started = time.monotonic()
    while time.monotonic()-started < 35:
        state = page.evaluate('({x:race.x,y:race.y,heading:race.heading,laps:race.laps,gate:race.gate})')
        if state['laps'] >= 1:
            break
        angle = math.atan2((state['y']-345)/210, (state['x']-500)/340) + .35
        x, y = 500+340*math.cos(angle), 345+210*math.sin(angle)
        desired = math.atan2(y-state['y'], x-state['x'])
        error = math.atan2(math.sin(desired-state['heading']), math.cos(desired-state['heading']))
        key = 'ArrowRight' if error > .07 else 'ArrowLeft' if error < -.07 else None
        if key != held:
            if held:
                page.keyboard.up(held)
            if key:
                page.keyboard.down(key)
            held = key
        page.wait_for_timeout(80)
    if held:
        page.keyboard.up(held)
    assert state['laps'] >= 1, f'Kart failed to complete a lap with arrow keys: {state}'
    page.evaluate('burst(100,100,"#fff",16)')
    page.wait_for_function('particles.length===0',timeout=2000)
    page.get_by_role('button',name='Arkaden',exact=True).click()
    page.get_by_role('button',name='Lumen',exact=False).click()
    page.locator('#mode').select_option('chill')
    page.get_by_role('button',name='Prova demo utan cykel').click()
    page.locator('#demowatts').fill('0')
    stopped=page.evaluate('flight.distance')
    page.wait_for_timeout(1200)
    assert page.evaluate('flight.distance')==stopped
    page.evaluate('flight.distance=31000;updateExtraHUD()')
    expect(page.locator('#hudsecondarylabel')).to_have_text('EXPEDITION · NÄSTA 500 M')
    assert page.locator('#hudenergy').evaluate('(element)=>element.value')<100
    assert not errors, errors
    print('Review fixes passed: mobile layout, sidebar arrows, full kart lap, particle cleanup and zero-watt cave stop.')
    browser.close()
