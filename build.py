#!/usr/bin/env python3
"""Build / (English) and /el/ (Greek) from _src/template.html.
The template holds English text with Greek in data-el attributes."""
import re, pathlib
ROOT = pathlib.Path(__file__).parent
tpl = (ROOT / '_src' / 'template.html').read_text(encoding='utf-8')
D = 'https://www.soulbunsandballs.com'

META = {
 'en': dict(lang='en', title='Soul Buns &amp; Balls | Smash Burgers in Kalamata',
   desc='Smash burger bar in Kalamata, Greece. Smash &amp; classic beef burgers, homemade sauces, crunchy fries. Tue–Sun from 18:00 until sold out. Anagnostara 3 · order via Wolt.',
   ogdesc='Smash burgers done right. Anagnostara 3, Kalamata. Tue–Sun from 18:00 until sold out. Dine in, takeaway and Wolt delivery.',
   url=f'{D}/', locale='en_US', btn='ΕΛ', other='/el/', btnlabel='Ελληνικά'),
 'el': dict(lang='el', title='Soul Buns &amp; Balls | Smash Burgers στην Καλαμάτα',
   desc='Smash burger bar στην Καλαμάτα. Smash &amp; κλασικά μοσχαρίσια burgers, σπιτικές σάλτσες, τραγανές πατάτες. Τρ–Κυ από τις 18:00 έως sold out. Αναγνωσταρά 3 · παραγγελία μέσω Wolt.',
   ogdesc='Smash burgers όπως πρέπει. Αναγνωσταρά 3, Καλαμάτα. Τρ–Κυ από τις 18:00 έως sold out. Στο μπαρ, πακέτο ή Wolt.',
   url=f'{D}/el/', locale='el_GR', btn='EN', other='/', btnlabel='English'),
}

def build(lang):
    m = META[lang]; s = tpl
    if lang == 'el':
        # swap every data-el element's inner HTML with the Greek text
        def swap(mt):
            open_tag, inner, close = mt.group(1), mt.group(3), mt.group(4)
            el = re.search(r'\sdata-el="([^"]*)"', open_tag).group(1)
            return open_tag + el + close
        # match <tag ... data-el="..." ...>INNER</tag> for non-nested simple elements, innermost first
        pat = re.compile(r'(<(\w+)[^>]*\sdata-el="[^"]*"[^>]*>)((?:(?!<\2[\s>]).)*?)(</\2>)', re.S)
        prev = None
        while prev != s:
            prev = s; s = pat.sub(swap, s)
    s = re.sub(r'\sdata-el="[^"]*"', '', s)
    s = s.replace('<html lang="en">', f'<html lang="{m["lang"]}">')
    s = re.sub(r'<title>.*?</title>', f'<title>{m["title"]}</title>', s)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{m["desc"]}">', s)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{m["title"]}">', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{m["ogdesc"]}">', s)
    s = re.sub(r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{m["title"]}">', s)
    s = re.sub(r'<meta property="og:locale" content="[^"]*">', f'<meta property="og:locale" content="{m["locale"]}">', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{m["url"]}">', s)
    s = re.sub(r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{m["url"]}">\n<link rel="alternate" hreflang="en" href="{D}/">\n<link rel="alternate" hreflang="el" href="{D}/el/">\n<link rel="alternate" hreflang="x-default" href="{D}/">', s)
    # language button becomes a link to the other version
    s = re.sub(r'<button type="button" class="lang" id="lang-toggle"[^>]*>[^<]*</button>',
        f'<a class="lang" id="lang-toggle" href="{m["other"]}" hreflang="{"el" if lang=="en" else "en"}" aria-label="{m["btnlabel"]}">{m["btn"]}</a>', s)
    s = s.replace('.lang{border:1px solid var(--rule);', '.lang{text-decoration:none;display:inline-block;border:1px solid var(--rule);')
    # replace the in-page toggle script with: remember choice + optional first-visit redirect
    s = re.sub(r"  var html=document\.documentElement, btn=document\.getElementById\('lang-toggle'\);\n  var els=.*?btn\.addEventListener\('click',function\(\)\{setLang\(html\.lang==='el'\?'en':'el'\);\}\);\n",
        "  var html=document.documentElement;\n"
        "  var lnk=document.getElementById('lang-toggle');\n"
        "  lnk.addEventListener('click',function(){try{localStorage.setItem('sbb-lang',html.lang==='el'?'en':'el');}catch(e){}});\n"
        + ("  try{var pref=localStorage.getItem('sbb-lang');if(!pref&&/^el/i.test(navigator.language||'')&&!/bot|crawl|spider/i.test(navigator.userAgent)){location.replace('/el/');}}catch(e){}\n" if lang=='en' else ''),
        s, flags=re.S)
    # JSON-LD: language-specific description + inLanguage
    if lang == 'el':
        s = s.replace('"description": "Independent burger restaurant in Kalamata, Greece, specializing in smash burgers, classic beef burgers, homemade sauces and crispy fries."',
                      '"description": "Ανεξάρτητο burger bar στην Καλαμάτα με smash burgers, κλασικά μοσχαρίσια burgers, σπιτικές σάλτσες και τραγανές πατάτες.",\n  "inLanguage": "el"')
        s = s.replace('"url": "https://www.soulbunsandballs.com/",', '"url": "https://www.soulbunsandballs.com/el/",')
        s = s.replace('"hasMenu": "https://www.soulbunsandballs.com/#menu"', '"hasMenu": "https://www.soulbunsandballs.com/el/#menu"')
        # relative asset paths from /el/
        for a in ['tagline.png','botm.jpg','avatar.png','logo.png','ig1.jpg','ig2.jpg','ig3.jpg']:
            s = s.replace(f'src="{a}"', f'src="/{a}"')
        s = s.replace('href="avatar.png"', 'href="/avatar.svg"')
        s = s.replace("b.textContent=(html.lang==='el'?'Έγινε':'Copied')", "b.textContent='Έγινε'")
    assert 'data-el' not in s and 'lang-toggle' in s
    return s

(ROOT / 'index.html').write_text(build('en'), encoding='utf-8')
(ROOT / 'el').mkdir(exist_ok=True)
(ROOT / 'el' / 'index.html').write_text(build('el'), encoding='utf-8')
(ROOT / 'sitemap.xml').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url><loc>{D}/</loc><xhtml:link rel="alternate" hreflang="en" href="{D}/"/><xhtml:link rel="alternate" hreflang="el" href="{D}/el/"/><xhtml:link rel="alternate" hreflang="x-default" href="{D}/"/></url>
  <url><loc>{D}/el/</loc><xhtml:link rel="alternate" hreflang="en" href="{D}/"/><xhtml:link rel="alternate" hreflang="el" href="{D}/el/"/><xhtml:link rel="alternate" hreflang="x-default" href="{D}/"/></url>
</urlset>
''', encoding='utf-8')
print('built / and /el/')
