"""Keyboard-only menu flow and twin-shot special regression checks."""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:18765/game')
    page.get_by_role('button',name='Orbital',exact=False).click()
    expect(page.locator('#start')).to_be_focused()
    page.keyboard.press('ArrowUp')
    expect(page.locator('#menudifficulty')).to_be_focused()
    page.keyboard.press('ArrowLeft')
    expect(page.locator('#difficulty')).to_have_value('easy')
    page.keyboard.press('ArrowUp');page.keyboard.press('ArrowRight')
    expect(page.locator('#target')).to_have_value('105')
    page.keyboard.press('ArrowLeft')
    expect(page.locator('#target')).to_have_value('100')
    page.keyboard.press('ArrowUp');page.keyboard.press('ArrowRight')
    expect(page.locator('#mode')).to_have_value('chill')
    page.screenshot(path='/tmp/orbital-keyboard-menu.png',full_page=True)
    # Traverse the menu to demo and launch without clicking.
    for _ in range(4):page.keyboard.press('ArrowDown')
    expect(page.locator('#demo')).to_be_focused()
    page.keyboard.press('Enter')
    expect(page.locator('#overlay')).to_be_hidden()
    expect(page.locator('#watts')).to_have_text('90')
    result=page.evaluate('''() => {
      shots=[];energy=100;const count=enemies.length,rate=fireRate(),points=score;
      special();update(0);
      return {n:shots.length,offsets:shots.map(s=>s.x-player.x),count:enemies.length,
        expectedCount:count,score,points,rate:fireRate(),expectedRate:rate,boost:boostRemaining};
    }''')
    assert result['n']==2 and result['offsets']==[-10,10],result
    assert result['count']==result['expectedCount'] and result['score']==result['points'],result
    assert result['rate']==result['expectedRate'] and result['boost']==10,result
    page.get_by_role('button',name='Helskärm',exact=False).click()
    page.wait_for_function('document.fullscreenElement !== null')
    expect(page.locator('#hudenergytext')).to_contain_text('2×')
    page.screenshot(path='/tmp/orbital-twin-shots.png')
    page.keyboard.press('p')
    expect(page.locator('#start')).to_be_focused()
    old=page.evaluate('({x:player.x,t:boostRemaining})')
    page.keyboard.press('ArrowDown')
    expect(page.locator('#backmenu')).to_be_focused()
    page.wait_for_timeout(200)
    assert page.evaluate('player.x')==old['x']
    assert page.evaluate('boostRemaining')==old['t']
    page.keyboard.press('ArrowUp');page.keyboard.press('Enter')
    expect(page.locator('#overlay')).to_be_hidden()
    expired=page.evaluate('''() => {
      power=0;ratio=0;boostRemaining=10;player.invulnerable=100;
      update(5);const midway=boostRemaining;update(5);
      const ended=boostRemaining;
      power=100;ratio=1;shots=[];wasFiring=false;update(0);
      return {midway,ended,n:shots.length};
    }''')
    assert expired=={'midway':5,'ended':0,'n':1},expired
    page.evaluate('enemies=[];update(0)')
    expect(page.locator('#overtitle')).to_have_text('Sektorn säkrad')
    expect(page.locator('#choices button').nth(0)).to_be_focused()
    oldx=page.evaluate('player.x')
    page.keyboard.press('ArrowRight')
    expect(page.locator('#choices button').nth(1)).to_be_focused()
    assert page.evaluate('player.x')==oldx
    page.keyboard.press('Enter')
    expect(page.locator('#wave')).to_have_text('2')
    expect(page.locator('#lives')).to_have_text('∞')
    page.keyboard.press('p');page.keyboard.press('ArrowDown');page.keyboard.press('Enter')
    expect(page.locator('#overtitle')).to_have_text('Orbital')
    expect(page.locator('#menutarget')).to_be_visible()
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    print('Keyboard menus and twin shots passed: settings, fullscreen, pause, upgrades, unchanged fire rate, 10s duration, no screen wipe.')
    browser.close()
