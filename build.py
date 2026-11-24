#!/usr/bin/env python3
"""Build the whole site from _src/.

Sources
  _src/template.html  the page, English text with Greek in data-el attributes
  _src/botm.json      Burgers of the Month, newest first (first entry = this month)

Output
  /index.html, /el/index.html                              home, English and Greek
  /burger-of-the-month/, /el/burger-of-the-month/          archive of every monthly burger
  /sitemap.xml, /llms.txt

The menu in the Restaurant JSON-LD and in llms.txt is read back from the built
page, so prices and names cannot drift from what visitors see.
"""
import re, json, html, pathlib, datetime
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).parent
tpl = (ROOT / '_src' / 'template.html').read_text(encoding='utf-8')
BURGERS = json.loads((ROOT / '_src' / 'botm.json').read_text(encoding='utf-8'))['burgers']
D = 'https://www.soulbunsandballs.com'
TODAY = datetime.date.today().isoformat()

MONTHS = {
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'el': ['Ιανουάριος', 'Φεβρουάριος', 'Μάρτιος', 'Απρίλιος', 'Μάιος', 'Ιούνιος', 'Ιούλιος', 'Αύγουστος', 'Σεπτέμβριος', 'Οκτώβριος', 'Νοέμβριος', 'Δεκέμβριος'],
}
MONTHS_EL_ACC = ['Ιανουάριο', 'Φεβρουάριο', 'Μάρτιο', 'Απρίλιο', 'Μάιο', 'Ιούνιο', 'Ιούλιο', 'Αύγουστο', 'Σεπτέμβριο', 'Οκτώβριο', 'Νοέμβριο', 'Δεκέμβριο']

FLAG_GR = '<svg class="flag" viewBox="0 0 27 18" aria-hidden="true"><rect width="27" height="18" fill="#0d5eaf"/><g fill="#fff"><rect x="10" y="2" width="17" height="2"/><rect x="10" y="6" width="17" height="2"/><rect y="10" width="27" height="2"/><rect y="14" width="27" height="2"/><rect x="4" width="2" height="10"/><rect y="4" width="10" height="2"/></g></svg>'
FLAG_UK = '<svg class="flag" viewBox="0 0 60 30" aria-hidden="true"><clipPath id="t"><path d="M30 15h30v15zv15H0zH0V0zV0h30z"/></clipPath><path d="M0 0v30h60V0z" fill="#012169"/><path d="M0 0l60 30m0-30L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0l60 30m0-30L0 30" clip-path="url(#t)" stroke="#C8102E" stroke-width="4"/><path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/><path d="M30 0v30M0 15h60" stroke="#C8102E" stroke-width="6"/></svg>'

PATHS = {'home': {'en': '/', 'el': '/el/'},
         'archive': {'en': '/burger-of-the-month/', 'el': '/el/burger-of-the-month/'}}
_top3 = ', '.join(b['name'] for b in BURGERS[:3])
META = {
 'home': {
  'en': dict(title='Soul Buns &amp; Balls | Smash Burgers in Kalamata',
    desc='Smash burger bar in Kalamata, Greece. Smash &amp; classic beef burgers, homemade sauces, crunchy fries. Tue–Sun from 18:00. Anagnostara 3 · order via Wolt.',
    ogdesc='Smash burgers done right. Anagnostara 3, Kalamata. Tue–Sun from 18:00 until sold out. Dine in, takeaway and Wolt delivery.'),
  'el': dict(title='Soul Buns &amp; Balls | Smash Burgers στην Καλαμάτα',
    desc='Smash burger bar στην Καλαμάτα. Smash &amp; κλασικά burgers, σπιτικές σάλτσες, τραγανές πατάτες. Τρ–Κυ από τις 18:00. Αναγνωσταρά 3 · παραγγελία μέσω Wolt.',
    ogdesc='Smash burgers όπως πρέπει. Αναγνωσταρά 3, Καλαμάτα. Τρ–Κυ από τις 18:00 έως sold out. Στο μπαρ, πακέτο ή Wolt.'),
 },
 'archive': {
  'en': dict(title='Burger of the Month | Soul Buns &amp; Balls, Kalamata',
    desc=f'Every Burger of the Month from Soul Buns &amp; Balls in Kalamata, with photos and ingredients: {_top3} and more.',
    ogdesc='One new burger every month, served for that month only. See all of them, with ingredients.'),
  'el': dict(title='Burger του μήνα | Soul Buns &amp; Balls, Καλαμάτα',
    desc=f'Όλα τα Burgers του μήνα του Soul Buns &amp; Balls στην Καλαμάτα, με φωτογραφίες και υλικά: {_top3} και άλλα.',
    ogdesc='Ένα νέο burger κάθε μήνα, μόνο για εκείνον τον μήνα. Δες τα όλα, με τα υλικά τους.'),
 },
}
LOCALE = {'en': 'en_US', 'el': 'el_GR'}
T = {
 'en': dict(all='All burgers of the month', menu='See the full menu', h1='Burger of the Month',
            intro='Every month we make one new burger at our bar in Kalamata, and we serve it for that month only. Here are all of them so far.',
            alt='{name}, {when} Burger of the Month at Soul Buns & Balls, Kalamata', tag='Available all {month}'),
 'el': dict(all='Όλα τα burgers του μήνα', menu='Δες όλο το μενού', h1='Burger του μήνα',
            intro='Κάθε μήνα φτιάχνουμε ένα νέο burger στο μαγαζί μας στην Καλαμάτα και το σερβίρουμε μόνο εκείνον τον μήνα. Εδώ είναι όλα μέχρι σήμερα.',
            alt='{name}, Burger του μήνα {when} στο Soul Buns & Balls, Καλαμάτα', tag='Όλο τον {month}'),
}

# ───────────────────────── Burger of the Month ─────────────────────────
def when(b, lang):
    y, m = b['month'].split('-')
    return f"{MONTHS[lang][int(m) - 1]} {y}"

def card(b, lang, heading, current, tag='div'):
    """One burger: poster on the left, month, name and ingredient chips on the right."""
    m = int(b['month'].split('-')[1])
    alt = html.escape(T[lang]['alt'].format(name=b['name'], when=when(b, lang)), quote=True)
    img = (f'<picture><source type="image/webp" srcset="/{b["image"]}.webp">'
           f'<img src="/{b["image"]}.jpg" alt="{alt}" width="{b["w"]}" height="{b["h"]}" loading="lazy" decoding="async"></picture>')
    chips = ''.join(f'<li>{html.escape(i)}</li>' for i in b['ingredients'])
    extra = ''
    if current:
        note = b.get('note', {}).get(lang)
        if note:
            extra += f'\n          <p class="botm-note">{note}</p>'
        month = MONTHS['en'][m - 1] if lang == 'en' else MONTHS_EL_ACC[m - 1]
        extra += f'\n          <span class="tag">{T[lang]["tag"].format(month=month)}</span>'
    ident = f' id="{b["slug"]}"' if tag == 'article' else ''
    return f'''<{tag} class="botm"{ident}>
        <figure>{img}</figure>
        <div class="text">
          <p class="eyebrow">{when(b, lang)}</p>
          <{heading} class="botm-name">{html.escape(b["name"])}</{heading}>
          <ul class="ing">{chips}</ul>{extra}
        </div>
      </{tag}>'''

def archive_main(lang):
    t = T[lang]
    cards = '\n      '.join(card(b, lang, 'h2', i == 0, tag='article') for i, b in enumerate(BURGERS))
    return f'''
  <div class="wrap archive-head">
    <h1 class="page-title">{t["h1"]}</h1>
    <p>{t["intro"]}</p>
  </div>
  <div class="wrap archive-list">
      {cards}
  </div>
  <div class="wrap archive-foot"><a class="btn-outline" href="{PATHS["home"][lang]}#menu">{t["menu"]}</a></div>
'''

# ───────────────────────── Menu, read back from the built page ─────────────────────────
def _price(text):
    m = re.fullmatch(r'(\d+(?:[.,]\d+)?)\s*€', text.strip())
    return float(m.group(1).replace(',', '.')) if m else None

def _spans(node):
    out = []
    for sp in node.find_all('span', recursive=False):
        b = sp.find_all('b')[-1] if sp.find('b') else None
        price = _price(b.get_text()) if b else None
        full = sp.get_text(' ', strip=True)
        name = full[:full.rfind(b.get_text(strip=True))].strip() if b else full
        out.append(dict(name=name, price=price))
    return out

def parse_menu(page_html, lang):
    """→ [{'name': section, 'items': [{'name', 'desc', 'price'}]}] exactly as shown in #menu."""
    menu = BeautifulSoup(page_html, 'html.parser').select_one('#menu')
    sections = []
    for sub in menu.select('p.sub'):
        cur = dict(name=sub.get_text(strip=True), items=[]); sections.append(cur)
        for child in sub.find_next_sibling('div', class_='menu-group').find_all(recursive=False):
            cls = child.get('class', [])
            if 'inline-list' in cls:
                cur['items'] += [dict(i, desc=None) for i in _spans(child)]
            elif 'item' in cls:
                name = child.h3.get_text(strip=True)
                d = child.select_one('p.desc'); desc = d.get_text(strip=True) if d else None
                if child.select_one('.inline-list'):          # e.g. Soul Sauces: its own section
                    sections.append(dict(name=name, items=[dict(i, desc=None) for i in _spans(child.select_one('.inline-list'))]))
                    continue
                if child.select_one('a[href="#botm"]'):       # the monthly special
                    b = BURGERS[0]
                    cur['items'].append(dict(name=name, price=None, desc=f"{desc}. {when(b, lang)}: {b['name']} ({', '.join(b['ingredients'])})"))
                    continue
                variants = _spans(child.select_one('.price'))
                if len(variants) == 1 and not variants[0]['name']:
                    cur['items'].append(dict(name=name, desc=desc, price=variants[0]['price']))
                else:
                    cur['items'] += [dict(name=v['name'], desc=desc, price=v['price']) for v in variants]
    shown = len(re.findall(r'<b>\s*\d+(?:[.,]\d+)?\s*€\s*</b>', str(menu)))
    read = sum(1 for s in sections for i in s['items'] if i['price'] is not None)
    assert shown == read, f'menu: {shown} prices on the page but {read} read'
    return sections

def menu_schema(sections, lang, url):
    def item(i):
        o = {'@type': 'MenuItem', 'name': i['name']}
        if i['desc']: o['description'] = i['desc']
        if i['price'] is not None:
            o['offers'] = {'@type': 'Offer', 'price': f"{i['price']:.2f}", 'priceCurrency': 'EUR'}
        return o
    return {'@type': 'Menu', 'name': 'Soul Buns & Balls menu', 'url': url + '#menu', 'inLanguage': lang,
            'hasMenuSection': [{'@type': 'MenuSection', 'name': s['name'], 'hasMenuItem': [item(i) for i in s['items']]} for s in sections]}

def menu_text(sections):
    lines = []
    for s in sections:
        seen, parts = set(), []
        for i in s['items']:
            p = '' if i['price'] is None else f" {i['price']:g}"
            d = ''
            if i['desc'] and i['desc'] not in seen:
                seen.add(i['desc']); d = f" ({i['desc']})"
            parts.append(f"{i['name']}{p}{d}")
        lines.append(f"{s['name']}: {'; '.join(parts)}.")
    return '\n'.join(lines)

# ───────────────────────── Pages ─────────────────────────
LD_RE = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)

def render(lang, page):
    m = META[page][lang]; other_lang = 'el' if lang == 'en' else 'en'
    url = D + PATHS[page][lang]; home = PATHS['home'][lang]
    s = tpl
    if page == 'archive':
        s = re.sub(r'(<main id="top">).*?(</main>)', r'\1<!--ARCHIVE-->\2', s, flags=re.S)
    if lang == 'el':
        # swap every data-el element's inner HTML with the Greek text, innermost first
        def swap(mt):
            return mt.group(1) + re.search(r'\sdata-el="([^"]*)"', mt.group(1)).group(1) + mt.group(4)
        pat = re.compile(r'(<(\w+)[^>]*\sdata-el="[^"]*"[^>]*>)((?:(?!<\2[\s>]).)*?)(</\2>)', re.S)
        prev = None
        while prev != s:
            prev = s; s = pat.sub(swap, s)
    s = re.sub(r'\sdata-el="[^"]*"', '', s)
    s = s.replace('<html lang="en">', f'<html lang="{lang}">')

    # generated content
    if page == 'home':
        more = f'\n      <p class="botm-more"><a class="btn-outline" href="{PATHS["archive"][lang]}">{T[lang]["all"]}</a></p>\n'
        s = re.sub(r'<!--BOTM-CURRENT.*?-->\n', lambda _: card(BURGERS[0], lang, 'h3', True) + more, s, count=1, flags=re.S)
    else:
        s = s.replace('<!--ARCHIVE-->', archive_main(lang))
        s = s.replace('href="#top"', f'href="{home}"')
        for a in ('#menu', '#instagram', '#find-us'):
            s = s.replace(f'href="{a}"', f'href="{home}{a}"')

    # head
    s = re.sub(r'<title>.*?</title>', f'<title>{m["title"]}</title>', s)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{m["desc"]}">', s)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{m["title"]}">', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{m["ogdesc"]}">', s)
    s = re.sub(r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{m["title"]}">', s)
    s = re.sub(r'<meta property="og:locale" content="[^"]*">', f'<meta property="og:locale" content="{LOCALE[lang]}">', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s)
    if page == 'archive':
        s = s.replace('<meta property="og:type" content="restaurant.restaurant">', '<meta property="og:type" content="website">')
    en_url, el_url = D + PATHS[page]['en'], D + PATHS[page]['el']
    s = re.sub(r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{url}">\n<link rel="alternate" hreflang="en" href="{en_url}">\n<link rel="alternate" hreflang="el" href="{el_url}">\n<link rel="alternate" hreflang="x-default" href="{en_url}">', s)

    # language button becomes a link to the same page in the other language
    other = PATHS[page][other_lang]
    s = re.sub(r'<button type="button" class="lang" id="lang-toggle"[^>]*>[^<]*</button>',
        f'<a class="lang" id="lang-toggle" href="{other}" hreflang="{other_lang}" aria-label="{"Ελληνικά" if lang == "en" else "English"}">{FLAG_GR if lang == "en" else FLAG_UK}</a>', s)
    s = s.replace('.lang{border:1px solid var(--rule);', '.lang{text-decoration:none;display:inline-flex;align-items:center;line-height:0;border:1px solid var(--rule);')
    s = s.replace('/* Hero */', '.flag{width:22px;height:auto;border-radius:2px;display:block}\n\n/* Hero */', 1)
    # replace the in-page toggle script with: remember the choice + first-visit redirect for Greek browsers
    s, n = re.subn(r"  var html=document\.documentElement, btn=document\.getElementById\('lang-toggle'\);\n  var els=.*?btn\.addEventListener\('click',function\(\)\{setLang\(html\.lang==='el'\?'en':'el'\);\}\);\n",
        lambda _: "  var html=document.documentElement;\n"
        "  var lnk=document.getElementById('lang-toggle');\n"
        "  lnk.addEventListener('click',function(){try{localStorage.setItem('sbb-lang',html.lang==='el'?'en':'el');}catch(e){}});\n"
        + (f"  try{{var pref=localStorage.getItem('sbb-lang');if(!pref&&/^el/i.test(navigator.language||'')&&!/bot|crawl|spider/i.test(navigator.userAgent)){{location.replace('{other}'+location.hash);}}}}catch(e){{}}\n" if lang == 'en' else ''),
        s, flags=re.S)
    assert n == 1
    if lang == 'el':
        s = s.replace("b.textContent=(html.lang==='el'?'Έγινε':'Copied')", "b.textContent='Έγινε'")

    # structured data
    sections = None
    ld = json.loads(LD_RE.search(s).group(2))
    if page == 'home':
        sections = parse_menu(s, lang)
        ld['url'] = url
        ld['hasMenu'] = menu_schema(sections, lang, url)
        if lang == 'el':
            ld['description'] = 'Ανεξάρτητο burger bar στην Καλαμάτα με smash burgers, κλασικά μοσχαρίσια burgers, σπιτικές σάλτσες και τραγανές πατάτες.'
            ld['inLanguage'] = 'el'
    else:
        ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', '@id': url + '#page', 'url': url,
              'name': html.unescape(m['title']), 'description': html.unescape(m['desc']), 'inLanguage': lang,
              'about': {'@type': 'Restaurant', '@id': D + '/#restaurant', 'name': 'Soul Buns & Balls', 'url': D + '/'},
              'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(BURGERS), 'itemListElement': [
                  {'@type': 'ListItem', 'position': i + 1, 'item': {
                      '@type': 'MenuItem', 'name': b['name'], 'description': f"{when(b, lang)}: {', '.join(b['ingredients'])}",
                      'image': f"{D}/{b['image']}.jpg", 'url': f"{url}#{b['slug']}"}}
                  for i, b in enumerate(BURGERS)]}}
    s = LD_RE.sub(lambda mt: mt.group(1) + '\n' + json.dumps(ld, ensure_ascii=False, indent=2) + '\n' + mt.group(3), s, count=1)

    assert 'data-el' not in s and 'lang-toggle' in s and '<!--BOTM' not in s and '<!--ARCHIVE' not in s
    return s, sections

def llms(menu_en, menu_el):
    cur = BURGERS[0]
    past = '\n'.join(f"- {when(b, 'en')}: {b['name']} — {', '.join(b['ingredients'])}" for b in BURGERS[1:])
    return f'''# Soul Buns & Balls

> Independent smash burger bar in Kalamata, Greece. Short menu, fresh daily, open Tuesday to Sunday from 18:00 until sold out. No reservations: first come, first served.

- Address: Anagnostara 3, Kalamata 24100, Greece
- Phone: +30 2721 303682
- Email: soulbunsandballs@gmail.com
- Hours: Tuesday–Sunday from 18:00 until sold out; closed Monday. Quantities are limited: come close to 18:00 or call to be sure.
- Service: dine in at the bar, takeaway, delivery via Wolt (https://wolt.com/el/grc/kalamata/restaurant/soul-buns-balls)
- Instagram: https://www.instagram.com/soulbunsandballs/
- Facebook: https://www.facebook.com/soulbunsandballs/

## Menu (prices in EUR)
{menu_text(menu_en)}

## Burger of the Month — {when(cur, 'en')}
{cur['name']}: {', '.join(cur['ingredients'])}.
One new burger every month, served for that month only.

## Past Burgers of the Month
{past}

## Pages
- Home and menu (English): {D}/
- Home and menu (Greek): {D}/el/
- Burger of the Month archive, with photos (English): {D}/burger-of-the-month/
- Burger of the Month archive (Greek): {D}/el/burger-of-the-month/

## Στα ελληνικά
Το Soul Buns & Balls είναι ανεξάρτητο smash burger bar στην Καλαμάτα (Αναγνωσταρά 3, 24100). Ανοιχτά Τρίτη–Κυριακή από τις 18:00 έως sold out· Δευτέρα κλειστά. Χωρίς κρατήσεις. Φαγητό στο μπαρ, πακέτο ή delivery μέσω Wolt. Τηλέφωνο +30 2721 303682.
Burger του μήνα ({when(cur, 'el')}): {cur['name']}.

Μενού (τιμές σε EUR)
{menu_text(menu_el)}
'''

def main():
    menus = {}
    for page in ('home', 'archive'):
        for lang in ('en', 'el'):
            out, sections = render(lang, page)
            path = ROOT / PATHS[page][lang].strip('/') / 'index.html'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(out, encoding='utf-8')
            if sections: menus[lang] = sections
    def entry(page, lang):
        alts = ''.join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{D}{PATHS[page][l]}"/>' for h, l in (('en', 'en'), ('el', 'el'), ('x-default', 'en')))
        return f'  <url><loc>{D}{PATHS[page][lang]}</loc><lastmod>{TODAY}</lastmod>{alts}</url>'
    (ROOT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + '\n'.join(entry(p, l) for p in ('home', 'archive') for l in ('en', 'el')) + '\n</urlset>\n', encoding='utf-8')
    (ROOT / 'llms.txt').write_text(llms(menus['en'], menus['el']), encoding='utf-8')
    print(f'built 4 pages, {len(BURGERS)} burgers of the month, {sum(len(s["items"]) for s in menus["en"])} menu items')

if __name__ == '__main__':
    main()
