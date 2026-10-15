"""Run with: uv run --with playwright python tests/browser_check.py.
Requires /usr/bin/chromium and a running local bridge. Workout history is not mutated.
"""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:18765/game')
    page.screenshot(path='/tmp/orbital-menu.png',full_page=True)
    page.get_by_role('button',name='Prova demo utan cykel').click()
    expect(page.locator('#overlay')).to_be_hidden()
    expect(page.locator('#watts')).to_have_text('90')
    rates = page.evaluate('''() => {
        const oldPower=power,oldRatio=ratio,oldBonus=fireBonus;
        fireBonus=1;power=1;
        const values=[0.5,0.75,1,1.5].map(r=>{ratio=Math.min(1,r);return fireRate()});
        power=0;values.push(fireRate());power=oldPower;ratio=oldRatio;fireBonus=oldBonus;
        return values;
    }''')
    assert abs(rates[0]-.8125)<.001 and rates[1]<3.4 and rates[2]==rates[3]==10 and rates[4]==0
    page.wait_for_timeout(1000)
    page.keyboard.press('p')
    expect(page.locator('#overlay')).to_be_visible()
    page.get_by_role('button',name='Återuppta',exact=True).click()
    expect(page.locator('#overlay')).to_be_hidden()
    x = page.evaluate('player.x')
    page.keyboard.down('ArrowLeft'); page.wait_for_timeout(300); page.keyboard.up('ArrowLeft')
    assert page.evaluate('player.x') < x
    page.evaluate('energy = 100')
    page.wait_for_timeout(100)
    expect(page.locator('#special')).to_have_text('★ SPECIAL REDO · Space')
    page.screenshot(path='/tmp/orbital-special-ready.png',full_page=True)
    page.keyboard.press('Space')
    expect(page.locator('#overtitle')).to_have_text('Sektorn säkrad')
    page.get_by_role('button',name='Snabbare eld',exact=False).click()
    expect(page.locator('#wave')).to_have_text('2')
    page.screenshot(path='/tmp/orbital-playing.png',full_page=True)
    page.get_by_role('button',name='Spelmeny',exact=True).click()
    page.locator('#mode').select_option('chill')
    page.get_by_role('button',name='Prova demo utan cykel').click()
    expect(page.locator('#lives')).to_have_text('∞')
    page.evaluate('player.invulnerable=0; hit()')
    assert page.evaluate('phase') == 'playing'
    page.get_by_role('button',name='Spelmeny',exact=True).click()
    page.locator('#mode').select_option('interval')
    page.get_by_role('button',name='Prova demo utan cykel').click()
    page.evaluate('energy=100; special()')
    expect(page.locator('#overtitle')).to_have_text('Sektorn säkrad')
    page.get_by_role('button',name='Energicell',exact=False).click()
    assert page.evaluate('phase') == 'rest'
    page.get_by_role('button',name='Spelmeny',exact=True).click()
    page.route('**/api/state', lambda route: route.fulfill(json={'connected':False,'metrics':{}}))
    page.wait_for_timeout(700)
    page.get_by_role('button',name='Starta uppdrag').click()
    expect(page.locator('#overlay')).to_be_visible()
    page.get_by_role('button',name='Återuppta',exact=True).click()
    expect(page.locator('#overtext')).to_contain_text('Väntar på färsk')
    page.goto('http://127.0.0.1:18765/dashboard')
    expect(page.locator('#status')).not_to_have_text('Hämtar träningslogg…')
    assert 'Ingen kontakt' not in page.locator('#status').inner_text()
    page.screenshot(path='/tmp/bikeerg-dashboard.png',full_page=True)
    # Empty history and selected-session views using synthetic data only.
    page.route('**/api/sessions',lambda r:r.fulfill(json=[]))
    page.reload(); expect(page.locator('#empty')).to_be_visible()
    session={'id':999,'started':1700000000,'ended':1700000060,'duration_s':60,'distance_m':500,'avg_power':100,'max_power':150,'avg_cadence':60,'samples':3}
    page.route('**/api/sessions',lambda r:r.fulfill(json=[session]))
    page.route('**/api/sessions/999',lambda r:r.fulfill(json={**session,'points':[{'t':1700000000+i*30,'power':v,'cadence':60} for i,v in enumerate([80,150,70])]}))
    page.reload();expect(page.locator('#detail')).to_be_visible()
    expect(page.locator('#detailStats')).to_contain_text('100 W')
    assert page.locator('#powerChart path').count() == 5
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.goto('http://127.0.0.1:18765/game')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    print('Browser checks passed: controls, demo, special, upgrades, modes, disconnect, dashboard, mobile layout.')
    browser.close()
