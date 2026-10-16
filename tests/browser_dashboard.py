"""Calendar totals, calorie equivalents and efficient detail refresh with synthetic data."""
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright, expect


def total(sessions, minutes, metres, calories, coverage):
    return {'sessions':sessions,'duration_s':minutes*60,'distance_m':metres,
            'calories_kcal':calories,'calorie_coverage':coverage,'max_power':220}


session={'id':999,'started':1700000000,'ended':1700000060,'duration_s':60,
         'distance_m':500,'avg_power':100,'max_power':150,'avg_cadence':60,
         'samples':3,'power_samples':3,'cadence_samples':3,'calories_kcal':2}
points=[{'t':1700000000,'power':80,'cadence':60,'gap':False},
        {'t':1700000001,'power':150,'cadence':65,'gap':False},
        {'t':1700000010,'power':70,'cadence':55,'gap':True}]

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1400,'height':1000})
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.route('**/api/sessions',lambda route:route.fulfill(json=[session]))
    page.route('**/api/sessions/999',lambda route:route.fulfill(json={**session,'points':points,'points_total':3}))
    def overview(route):
        period=parse_qs(urlsplit(route.request.url).query).get('period',['week'])[0]
        bins=[{'label':f'2026-10-{12+i:02d}',**total(1,10,100,100,1)} for i in range(7)]
        route.fulfill(json={'period':period,'title':period,'start':'2026-10-12','end_exclusive':'2026-10-19',
            'timezone':'CEST','attribution':'Pass räknas vid start.',
            'current':total(205,300,20500,1500,200),
            'previous':None if period=='lifetime' else total(100,200,10000,1000,100),
            'bins':bins,'previous_bins':[] if period=='lifetime' else bins})
    page.route('**/api/overview*',overview)
    page.goto('http://127.0.0.1:18765/dashboard')
    expect(page.locator('#count')).to_have_text('205')
    expect(page.locator('#calories')).to_have_text('1 500 kcal')
    expect(page.locator('#equivalentValue')).to_contain_text('10 öl')
    expect(page.locator('#equivalentNote')).to_contain_text('200 av 205')
    expect(page.locator('#detail')).to_be_visible()
    assert page.locator('#powerChart path').last.get_attribute('d').count('M')==2
    button=page.locator('.session').first
    button.focus()
    page.evaluate('refresh()')
    assert page.evaluate('document.activeElement?.classList.contains("session")')
    page.locator('#period').select_option('month')
    expect(page.locator('#monthWrap')).to_be_visible()
    expect(page.locator('#periodNote')).to_contain_text('month')
    page.locator('#period').select_option('year')
    expect(page.locator('#yearWrap')).to_be_visible()
    page.locator('#period').select_option('lifetime')
    expect(page.locator('#current')).to_be_hidden()
    page.locator('#equivalent').select_option('banana')
    expect(page.locator('#equivalentValue')).to_contain_text('bananer')
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='/tmp/bikeerg-dashboard-synthetic.png',full_page=True)
    assert not errors,errors
    print('Dashboard checks passed: all periods, full-history cards, calorie comparison, gap chart, focus and mobile layout.')
    browser.close()
