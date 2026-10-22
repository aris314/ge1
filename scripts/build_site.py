from pathlib import Path
from html import escape
import shutil
import re

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = ROOT / "members"
OUTPUT = ROOT / "_site"

html = (ROOT / "index.html").read_text(encoding="utf-8")
cv_files = sorted(MEMBERS.glob("*.html"))


def prettify_name(filename_stem):
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", filename_stem)
    return name.replace("_", " ").replace("-", " ").strip()


def initials_for(name):
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper() if name else "CV"


cards = []
for cv in cv_files:
    name = prettify_name(cv.stem)
    initials = initials_for(name)
    cards.append(f'''<article class="card">
  <div class="avatar">{escape(initials)}</div>
  <h2>{escape(name)}</h2>
  <p>Μέλος της ομάδας</p>
  <a class="btn" href="members/{escape(cv.name, quote=True)}"
     target="_blank" rel="noopener noreferrer">Δες το βιογραφικό →</a>
</article>''')

if "<!-- CV_LINKS -->" not in html:
    raise ValueError("Δεν βρέθηκε το σημείο <!-- CV_LINKS --> στο index.html")
html = html.replace("<!-- CV_LINKS -->", "\n".join(cards))

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir(parents=True)
(OUTPUT / "index.html").write_text(html, encoding="utf-8")
output_members = OUTPUT / "members"
shutil.copytree(MEMBERS, output_members)

style = '''<style>
.sdy60-webring {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin: 20px auto;
  padding: 12px;
  font-family: 'Segoe UI', Arial, sans-serif;
}
.sdy60-webring a {
  display: inline-block;
  padding: 10px 15px;
  border-radius: 10px;
  background: #7568d8;
  color: white;
  text-decoration: none;
}
.sdy60-webring a:hover { background: #2800a8; }
</style>'''

for i, cv in enumerate(cv_files):
    previous_cv = cv_files[(i - 1) % len(cv_files)]
    next_cv = cv_files[(i + 1) % len(cv_files)]
    page = output_members / cv.name
    cv_html = page.read_text(encoding="utf-8")

    navigation = f'''<nav class="sdy60-webring" aria-label="Πλοήγηση στα βιογραφικά της ομάδας">
  <a href="{escape(previous_cv.name, quote=True)}">← Προηγούμενο</a>
  <a href="../index.html">Ομάδα ΣΔΥ60</a>
  <a href="{escape(next_cv.name, quote=True)}">Επόμενο →</a>
</nav>'''

    # Εισαγωγή CSS μια φορά
    if re.search(r"</head\s*>", cv_html, flags=re.IGNORECASE):
        cv_html = re.sub(r"</head\s*>", lambda m: style + "\n" + m.group(0),
                         cv_html, count=1, flags=re.IGNORECASE)
    else:
        cv_html = style + "\n" + cv_html

    # Εύρεση του κύριου container και του αντίστοιχου κλεισίματος div.
    # Μετράμε εμφωλευμένα div ώστε η δεύτερη μπάρα να μπει μέσα στο πλαίσιο.
    container_match = re.search(
        r'<div\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\bcontainer\b[^"\']*["\'])[^>]*>',
        cv_html, flags=re.IGNORECASE
    )
    if container_match:
        opening_end = container_match.end()
        depth = 1
        closing_start = None
        for match in re.finditer(r'</?div\b[^>]*>', cv_html[opening_end:], flags=re.IGNORECASE):
            if match.group(0).lower().startswith('</div'):
                depth -= 1
            else:
                depth += 1
            if depth == 0:
                closing_start = opening_end + match.start()
                break
        if closing_start is None:
            raise ValueError(f"Δεν βρέθηκε το κλείσιμο του container στο {cv.name}")
        # Πρώτα εισάγουμε την κάτω μπάρα για να διατηρηθούν οι θέσεις χαρακτήρων.
        cv_html = cv_html[:closing_start] + "\n" + navigation + "\n" + cv_html[closing_start:]
        cv_html = cv_html[:opening_end] + "\n" + navigation + "\n" + cv_html[opening_end:]
    else:
        body_open = re.search(r'<body\b[^>]*>', cv_html, flags=re.IGNORECASE)
        body_close = re.search(r'</body\s*>', cv_html, flags=re.IGNORECASE)
        if not body_open or not body_close:
            raise ValueError(f"Δεν βρέθηκε έγκυρο body στο {cv.name}")
        cv_html = cv_html[:body_close.start()] + "\n" + navigation + "\n" + cv_html[body_close.start():]
        cv_html = cv_html[:body_open.end()] + "\n" + navigation + "\n" + cv_html[body_open.end():]

    page.write_text(cv_html, encoding="utf-8")

print(f"Η ιστοσελίδα δημιουργήθηκε με {len(cv_files)} βιογραφικά και δύο Webring ανά βιογραφικό.")
print("Φάκελος βιογραφικών:", MEMBERS)
print("Βιογραφικά που βρέθηκαν:", len(cv_files))
print("Φάκελος εξόδου:", OUTPUT)
for cv in cv_files:
    generated = OUTPUT / "members" / cv.name
    content = generated.read_text(encoding="utf-8")
    print(cv.name, "→ Μενού:", "Προηγούμενο" in content)
