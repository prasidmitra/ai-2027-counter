#!/usr/bin/env python3
"""Build index.html from content/*.txt (Markdown-ish) into the AI-2030 counter page."""
import re, os

BASE = os.path.dirname(os.path.abspath(__file__))

def inline(s: str, linkify: bool = True) -> str:
    # Link standalone "*AI 2027*" mentions to the original site (underlined, non-blue).
    # The "*AI 2027? ...Nah.*" title is untouched because of the trailing "?".
    if linkify:
        s = re.sub(r'\*AI 2027\*', r'<a href="https://ai-2027.com/">AI 2027</a>', s)
    # bold first (handles nested *italic* inside **bold**)
    s = re.sub(r'\*\*(.+?)\*\*',
               lambda m: '<strong>' + re.sub(r'\*(.+?)\*', r'<em>\1</em>', m.group(1)) + '</strong>',
               s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    return s

def autolink(s: str) -> str:
    return re.sub(r'(https?://[^\s\)\]]+)', r'<a href="\1">\1</a>', s)

def slug(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def para(s: str, cls=None) -> str:
    c = f' class="{cls}"' if cls else ''
    return f'<p{c}>{inline(autolink(s))}</p>'

# ----------------------------------------------------------------------------
# Essay body
# ----------------------------------------------------------------------------
def build_essay() -> str:
    lines = open(os.path.join(BASE, 'content', 'essay.txt'), encoding='utf-8').read().splitlines()

    title_full = lines[0][2:].strip()            # "AI 2030: The Limits of Intelligence"
    main_title = "AI 2027? ...Nah."              # site name (user-chosen)
    sub_title = title_full.split(':', 1)[1].strip() if ':' in title_full else ''

    # Robustly locate subtitle (*...*), date (**...**), and the first `## ` heading.
    subtitle, date, start = '', '', 0
    for n in range(1, len(lines)):
        s = lines[n].strip()
        if s.startswith('*') and s.endswith('*') and not s.startswith('**'):
            subtitle = s.strip('*')
        elif s.startswith('**') and s.endswith('**'):
            date = s.strip('*')
        elif s.startswith('## '):
            start = n
            break

    meta = dict(main=main_title, sub=sub_title, subtitle=inline(subtitle), date=inline(date))

    sections = []
    cur = None
    for line in lines[start:]:
        line = line.rstrip()
        if line.startswith('## '):
            cur = {'heading': line[3:].strip(), 'blocks': []}
            sections.append(cur)
        elif not line.strip():
            continue
        elif re.fullmatch(r'\*\*[^*]+\*\*', line.strip()):
            cur['blocks'].append(('statement', line.strip()[2:-2]))
        else:
            cur['blocks'].append(('p', line.strip()))

    out = []
    for sec in sections:
        sid = slug(sec['heading'])
        out.append(f'<section id="{sid}">')
        out.append(f'<h2>{sec["heading"]}</h2>')
        for kind, text in sec['blocks']:
            if kind == 'statement':
                out.append(f'<p class="statement">{inline(text)}</p>')
            else:
                out.append(para(text))
        out.append('</section>')
    return meta, '\n'.join(out)

# ----------------------------------------------------------------------------
# Appendix (notes) body
# ----------------------------------------------------------------------------
def build_notes() -> str:
    raw = open(os.path.join(BASE, 'content', 'more notes.txt'), encoding='utf-8').read().splitlines()
    # Everything after the final `---` separator is the author's note (handled separately).
    last_sep = max(n for n, l in enumerate(raw) if l.strip() == '---')
    lines = raw[:last_sep]

    # Split at the "## " headings to build sections.
    sections = []          # list of (heading, [lines])
    cur = None
    for line in lines:
        if line.startswith('## '):
            cur = [line[3:].strip(), []]
            sections.append(cur)
        elif line.strip() == '---':
            continue
        elif cur is not None:
            cur[1].append(line.rstrip())

    out = []
    for heading, body in sections:
        sid = slug(heading)
        if heading == 'References and Further Reading':
            out.append(f'<section id="{sid}" class="references">')
            out.append(f'<h2>{heading}</h2>')
            out.append(render_references(body))
            out.append('</section>')
        else:
            out.append(f'<section id="{sid}">')
            out.append(f'<h2>{heading}</h2>')
            out.append(render_prose(body))
            out.append('</section>')

    return '\n'.join(out)

def render_prose(body):
    """Paragraphs + optional markdown table."""
    out = []
    i = 0
    while i < len(body):
        line = body[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            # collect table rows
            rows = []
            while i < len(body) and body[i].strip().startswith('|'):
                rows.append(body[i].strip())
                i += 1
            out.append(render_table(rows))
            continue
        out.append(para(line))
        i += 1
    return '\n'.join(out)

def render_table(rows):
    cells = [[c.strip() for c in r.strip('|').split('|')] for r in rows]
    header = cells[0]
    body = cells[2:]  # skip the |---|---| separator
    h = ''.join(f'<th>{inline(c)}</th>' for c in header)
    b = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>' for row in body)
    return ('<div class="table-wrapper"><table>'
            f'<thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')

def humanize_url(url: str) -> str:
    """Turn a URL's last path segment into a short, readable label."""
    slug = url.rstrip('/').split('/')[-1]
    words = re.sub(r'[-_+]+', ' ', slug).split()
    if not words:
        return url
    small = {'a', 'an', 'and', 'of', 'the', 'for', 'from', 'in', 'on', 'to', 'vs'}
    acronyms = {'ai', 'ifr', 'iea', 'nist', 'bcg'}
    out = []
    for w in words:
        lw = w.lower()
        if lw in acronyms:
            out.append(w.upper())
        elif lw in small:
            out.append(lw)
        else:
            out.append(w.capitalize())
    return ' '.join(out)

def render_references(body):
    out = []
    i = 0
    # leading intro paragraph(s): everything before the first category (pure-bold line)
    intro = []
    while i < len(body):
        line = body[i].strip()
        if not line:
            i += 1
            continue
        if re.fullmatch(r'\*\*[^*]+\*\*', line):
            break
        intro.append(line)
        i += 1
    for p in intro:
        out.append(para(p))

    while i < len(body):
        line = body[i].strip()
        if not line:
            i += 1
            continue
        if re.fullmatch(r'\*\*[^*]+\*\*', line):
            # Category heading -> link to the first source URL found in this category.
            category = line[2:-2]
            url = ''
            j = i + 1
            while j < len(body):
                nxt = body[j].strip()
                if re.fullmatch(r'\*\*[^*]+\*\*', nxt):
                    break  # next category reached first
                if nxt.startswith('http'):
                    url = nxt
                    break
                j += 1
            if url:
                out.append(f'<h4 class="ref-category"><a href="{url}" target="_blank" rel="noopener">{category}</a></h4>')
            else:
                out.append(f'<h4 class="ref-category">{category}</h4>')
            i += 1
        elif re.fullmatch(r'\*\*.*\*\*', line):
            # Citation -> plain text; its source URL is consumed by the category heading.
            out.append(f'<p class="ref-title">{inline(line, linkify=False)}</p>')
            j = i + 1
            while j < len(body) and not body[j].strip():
                j += 1
            if j < len(body) and body[j].strip().startswith('http'):
                i = j + 1  # skip the citation's source URL line
            else:
                i += 1
        elif line.startswith('http'):
            # Standalone URL (e.g. a "Relevant sections:" sub-link) -> named link.
            out.append(f'<a class="ref-link" href="{line}" target="_blank" rel="noopener">{humanize_url(line)}</a>')
            i += 1
        else:
            out.append(para(line))
            i += 1
    return '\n'.join(out)

# ----------------------------------------------------------------------------
# Author note (after the --- separator at end of notes file)
# ----------------------------------------------------------------------------
def build_author_note() -> str:
    lines = open(os.path.join(BASE, 'content', 'more notes.txt'), encoding='utf-8').read().splitlines()
    # find last '---' separator
    idx = [n for n, l in enumerate(lines) if l.strip() == '---'][-1]
    body = lines[idx + 1:]
    # drop leading blank lines
    while body and not body[0].strip():
        body.pop(0)
    heading = None
    paras = []
    for line in body:
        s = line.strip()
        if not s:
            continue
        if s.startswith('*') and s.endswith('*') and heading is None:
            heading = s.strip('*')
        else:
            paras.append(s)
    out = ['<div class="author-note">']
    out.append(f'<h3>{heading}</h3>')
    out.extend(para(p) for p in paras)
    out.append('</div>')
    return '\n'.join(out)

# ----------------------------------------------------------------------------
# Intro tab boxes ("What is this?" / "Who am I?")
# ----------------------------------------------------------------------------
def build_about() -> str:
    raw = open(os.path.join(BASE, 'content', 'about.txt'), encoding='utf-8').read().splitlines()
    sections = []
    cur = None
    for line in raw:
        if line.startswith('## '):
            cur = {'heading': line[3:].strip(), 'paras': []}
            sections.append(cur)
        elif line.strip():
            cur['paras'].append(line.strip())

    out = ['<div class="tab-boxes">']
    out.append('<div class="tab-tabs" role="tablist">')
    for i, sec in enumerate(sections):
        sid = slug(sec['heading'])
        active = ' active' if i == 0 else ''
        out.append(
            f'<button type="button" class="tab-btn{active}" role="tab" '
            f'aria-selected="{"true" if i == 0 else "false"}" '
            f'aria-controls="tab-panel-{sid}" id="tab-{sid}" data-tab="{sid}">{inline(sec["heading"])}</button>'
        )
    out.append('</div>')
    for i, sec in enumerate(sections):
        sid = slug(sec['heading'])
        open_cls = ' open' if i == 0 else ''
        out.append(f'<div class="tab-panel{open_cls}" id="tab-panel-{sid}" role="tabpanel" aria-labelledby="tab-{sid}">')
        for p in sec['paras']:
            out.append(f'<p>{inline(autolink(p))}</p>')
        out.append('</div>')
    out.append('</div>')
    return '\n'.join(out)

# ----------------------------------------------------------------------------
# Assemble
# ----------------------------------------------------------------------------
meta, essay_html = build_essay()
notes_html = build_notes()
about_html = build_about()

lede_paras = [
    "I argue that superintelligence doesn't automatically mean an imminent AI takeover. The physical world has constraints that intelligence alone cannot overcome overnight.",
    "Through a series of thought experiments, I explore why the road from superintelligence to human extinction may be far longer, messier, and more uncertain than *AI 2027* suggests.",
]
lede_html = '\n'.join(para(p) for p in lede_paras)

toc = []
for f in ['content/essay.txt', 'content/more notes.txt']:
    for line in open(os.path.join(BASE, f), encoding='utf-8'):
        if line.startswith('## '):
            h = line[3:].strip()
            toc.append((h, slug(h)))

toc_items = '\n'.join(f'<li><a href="#{s}">{h}</a></li>' for h, s in toc)

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI 2027? ...Nah.</title>
  <meta name="description" content="Why an Intelligence Explosion Does Not Mean an Imminent AI Takeover. A response to AI 2027." />
  <link rel="icon" href="favicon.ico?v=3" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png?v=3" />
  <link rel="icon" type="image/png" sizes="16x16" href="favicon-16x16.png?v=3" />
  <link rel="apple-touch-icon" href="apple-touch-icon.png?v=3" />
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <div class="page">

    <main class="article">
      <header class="site-header">
        <h1 class="site-title"><a href="#">{meta['main']}</a></h1>
        <p class="author"><a href="https://www.linkedin.com/in/prasidmitra/" target="_blank" rel="noopener">Prasid&nbsp;Mitra</a></p>
      </header>

{lede_html}

{about_html}

      <p class="published">Published {meta['date']}</p>

{essay_html}

{notes_html}

    </main>

    <aside class="sidebar">
      <nav class="contents" id="contents">
        <h2>Contents</h2>
        <ol>
{toc_items}
        </ol>
      </nav>
    </aside>
  </div>
  <script src="script.js"></script>
</body>
</html>
'''

open(os.path.join(BASE, 'index.html'), 'w', encoding='utf-8').write(page)
print(f'wrote index.html ({len(page)} bytes)')
print(f'sections: {len(toc)}')
