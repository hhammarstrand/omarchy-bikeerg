"""Arcade selection, additional engines, and identical fullscreen layout."""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:18765/game')
    expect(page.locator('#overtitle')).to_have_text('Välj ditt spel')
    expect(page.locator('.gamecard')).to_have_count(3)
    page.screenshot(path='/tmp/bikeerg-arcade-menu.png',full_page=True)
    page.keyboard.press('ArrowRight');page.keyboard.press('Enter')
    expect(page.locator('#overtitle')).to_have_text('Velodrift')
    page.get_by_role('button',name='Prova demo utan cykel').click()
    assert page.evaluate('currentGame')=='kart'
    page.wait_for_timeout(500)
    before=page.locator('.stage').bounding_box()
    page.get_by_role('button',name='Helskärm',exact=False).click()
    page.wait_for_function('document.fullscreenElement===document.documentElement')
    expect(page.locator('.side')).to_be_visible()
    expect(page.locator('header')).to_be_visible()
    after=page.locator('.stage').bounding_box()
    assert abs(before['width']/before['height']-after['width']/after['height'])<.01
    page.screenshot(path='/tmp/velodrift-fullscreen.png',full_page=True)
    page.evaluate('document.exitFullscreen()')
    rates=page.evaluate('''() => {
        const speeds=[];
        for(const watts of [50,100,200]){
            race.speed=0;power=watts;ratio=Math.min(1,watts/100);
            for(let i=0;i<50;i++){race.x=500;race.y=555;updateKart(.1)}
            speeds.push(race.speed);
        }
        return speeds;
    }''')
    assert rates[0]<rates[1] and abs(rates[1]-rates[2])<.001 and rates[1]<=145,rates
    steering=page.evaluate('''() => {race.heading=0;race.speed=100;keys.add('ArrowRight');updateKart(.1);keys.clear();return race.heading}''')
    assert steering>0
    page.keyboard.press('p')
    pos=page.evaluate('race.x')
    page.keyboard.press('ArrowDown');page.wait_for_timeout(100)
    assert page.evaluate('race.x')==pos
    page.keyboard.press('ArrowUp');page.keyboard.press('Enter')
    page.evaluate('''() => {
        mode='arcade';race.laps=0;race.gate=0;race.speed=0;
        for(let i=0;i<12;i++){const point=trackPoint(Math.PI+race.gate*Math.PI/2);race.x=point.x;race.y=point.y;updateKart(0)}
    }''')
    expect(page.locator('#overtitle')).to_have_text('Målgång!')
    page.get_by_role('button',name='Arkaden',exact=True).click()
    page.keyboard.press('ArrowRight');page.keyboard.press('ArrowRight');page.keyboard.press('Enter')
    expect(page.locator('#overtitle')).to_have_text('Lumen')
    page.get_by_role('button',name='Prova demo utan cykel').click()
    page.locator('#demowatts').fill('65')
    page.wait_for_timeout(700)
    lift=page.evaluate('''() => {
        const results=[];mode='chill';
        for(const r of [.3,.65,1]){flight.y=caveCenter(flight.distance+flight.x);flight.vy=0;ratio=r;updateCave(.1);results.push(flight.vy)}
        return results;
    }''')
    assert lift[0]>0 and abs(lift[1])<.0001 and lift[2]<0,lift
    page.screenshot(path='/tmp/lumen-playing.png',full_page=True)
    page.evaluate("mode='arcade';flight.distance=30000;updateCave(0)")
    expect(page.locator('#overtitle')).to_have_text('Ut i ljuset!')
    page.get_by_role('button',name='Arkaden',exact=True).click()
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.get_by_role('button',name='Velodrift',exact=False).click()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert not errors,errors
    print('Arcade checks passed: 3 games, keyboard selection, capped kart speed, steering, checkpoints, cave lift, goals, full-page fullscreen and mobile layout.')
    browser.close()
