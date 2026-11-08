#!/usr/bin/env python3
"""Familienchronik bauen: Datendatei → Buch (PDF/X-4 für die Druckerei, PDF/A-3 mit eingebetteten Daten),
offene Daten (GEDCOM 7 und 5.5.1, JSON mit Schema, JSONL, CSV, RO-Crate), bearbeitbare Fassung (ODT, Markdown).

Aufruf:  python3 build.py --daten meine-familie.js [--format A4|A5|B5|17x24|200x260|21x28|magazin|quadrat|letter|7x10|6x9|8x10|BxH]
                          [--bilder gross|kompakt] [--sprache de|en] [--ausgabe ordner] [--ohne-pdf]
Die Datendatei setzt window.FA (Schema: beispiel/erzeuge_demo.py). Alles Familienspezifische steht dort unter "buch".
Voraussetzungen: Python 3.10+, weasyprint, pillow, pyshp; node (liest die .js-Datei); pandoc für ODT/Markdown.
"""
import csv, hashlib, html, json, os, re, shutil, subprocess, sys, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PUB = os.path.dirname(os.path.abspath(sys.argv[sys.argv.index("--daten") + 1])) if "--daten" in sys.argv else os.path.join(ROOT, "public")
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- Format und Optionen ----------
# python3 build.py [--format A4|A5|B5|17x24|200x260|21x28|magazin|quadrat|letter|7x10|6x9|8x10|BxH] [--bilder gross|kompakt] [--sprache de|en] [--ohne-pdf]
FORMATE = {"A4": (210, 297), "A5": (148, 210), "B5": (176, 250), "17x24": (170, 240), "200x260": (200, 260), "21x28": (210, 280),
           "magazin": (230, 300), "quadrat": (210, 210), "letter": (215.9, 279.4), "7x10": (177.8, 254), "6x9": (152.4, 228.6), "8x10": (203.2, 254)}
def _opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else default
FMT = _opt("--format", "200x260")
if FMT in FORMATE:
    W, H = FORMATE[FMT]
else:
    W, H = (float(x) for x in FMT.lower().replace("mm", "").split("x"))
MI, MO, MT, MB = round(W * .12, 1), round(W * .11, 1), round(H * .085, 1), round(H * .10, 1)
TW = round(W - MI - MO, 1)          # Satzspiegelbreite
AH = round(H - MT - MB, 1)          # Satzspiegelhöhe
CW = round(min(TW, 124 * max(.9, min(1.05, W / 200))), 1)   # Lesespalte, rund 65 Zeichen
FS = round(10.8 * max(.93, min(1.06, W / 200)), 2)          # Grundschrift
BILDER = _opt("--bilder", "gross")
SPRACHE = _opt("--sprache", "de")

# ---------- Daten laden ----------
DATEN = os.path.abspath(_opt("--daten", os.path.join(PUB, "data.js")))
raw = subprocess.run(["node", "-e", "global.window={};require(process.argv[1]);process.stdout.write(JSON.stringify(window.FA))", DATEN],
                     capture_output=True, text=True, check=True).stdout
FA = json.loads(raw)
STAND = FA["stand"]  # TT.MM.JJJJ
ISO = "-".join(reversed(STAND.split(".")))
OUT = os.path.abspath(_opt("--ausgabe", os.path.join(PUB, "exports", f"paket-{ISO}")))
if os.path.exists(OUT):
    n = 2
    while os.path.exists(f"{OUT}-{n}"):
        n += 1
    OUT = f"{OUT}-{n}"
D = os.path.join(OUT, "daten"); B = os.path.join(OUT, "buch")
os.makedirs(D); os.makedirs(B)

P = FA["persons"]; S = {s["id"]: s for s in FA["sources"]}
LV = FA["levels"]

# ---------- Buchangaben: neutrale Standardwerte; die Familie setzt sie in der Datendatei unter "buch" ----------
BK = {
    "titel_html": "Familienchronik", "titel": "Familienchronik", "untertitel_html": "Eine belegte Familiengeschichte",
    "signatur": "DFA-XXX-01", "kurz": "DFA-XXX", "bildprefix": "Foto_", "bilderdir": os.path.join(PUB, "bilder"), "cover": "",
    "hg": "Zusammengestellt von …", "autor": "", "impressum_html": "<p>Privatdruck für die Familie.</p>",
    "vorwort_html": "<p class='lead'>Dieses Buch erzählt, wer diese Menschen waren, woher sie kamen und was sie erlebt haben.</p>",
    "karte_lead_html": "", "karte_hinweis": "Grenzen von heute.", "entfernungen": [], "regionen": [], "orte_extra": {}, "karte_bbox": None, "revier": False,
    "wurzeln": [], "familie_html": "<p>Was die Familie beigetragen hat: Fotos, Papiere, Erinnerungen, Entscheidungen.</p>",
    "rueck_html": "<p>Eine belegte Familiengeschichte. Jede Aussage nennt ihre Quelle.</p>",
    "gen_namen": None, "beispielbilder": [],
    # Pflicht für das Kolophon: tatsächliches Modell und Zeitraum eintragen
    "ki_name": "Claude, ein Programm der amerikanischen Firma Anthropic", "ki_modell": "Modellname eintragen", "ki_zeitraum": "im Zeitraum …",
}
BK.update(FA.get("buch", {}))
BK.setdefault("ki_html", "<p>Die KI hat Urkunden und Zeitungen gelesen und abgeschrieben, übersetzt, in Online-Archiven gesucht, Funde mit den Erinnerungen verglichen, Texte entworfen und das Buch gesetzt. Die Entscheidungen hat die Familie getroffen.</p>")
KURZ = BK["kurz"]; BPRE = BK["bildprefix"]; BDIR = BK["bilderdir"]
SICH_DEF = {"U": "belegt", "R": "belegt", "A": "sehr wahrscheinlich", "Z": "sehr wahrscheinlich", "F": "möglich", "B": "möglich",
            "E": "möglich", "L": "möglich", "H": "möglich", "O": "unklar"}
year = lambda d: (re.search(r"\d{4}", str(d or "")) or [""])[0] if d else ""

def privat(p):
    return p.get("living") or p.get("minor")

def datum(p, o):
    if not o or not o.get("d"):
        return ""
    return year(o["d"]) if privat(p) else o["d"]

def ort(p, o):
    if not o or not o.get("p"):
        return ""
    return o["p"].split(",")[0] if privat(p) else o["p"]

# ---------- Zitierweise ----------
def zitat(src_ref):
    """Fußnote in historischer Zitierweise: Urheber/Archiv, Titel, Bestand/Signatur bzw. Fundstelle, Abruf."""
    r = str(src_ref)
    m = re.match(r"^" + re.escape(KURZ) + r"-F(\d{4})(.*)$", r)
    if m:
        fr = FA.get("fronts", {}).get(m.group(1), ""); bk = FA.get("backs", {}).get(m.group(1), "")
        t = f"{BK['titel']} (Privatbesitz), Foto {KURZ}-F{m.group(1)}{m.group(2)}"
        if bk:
            t += f", Rückseite: „{bk}“"
        return t + "."
    sid = r.split(" ")[0]; rest = r[len(sid):].strip()
    s = S.get(sid)
    if not s:
        return r + "."
    teile = [s["title"]]
    if s.get("where"):
        teile.append(s["where"])
    if rest:
        teile.append(rest)
    z = ", ".join(teile)
    if s.get("url"):
        z += f", {s['url']}"
    if s.get("abruf"):
        z += f" (abgerufen {s['abruf']})"
    return z + "."

def zitat_lang(s):
    z = f"{s['title']}. {s.get('detail','')}".strip()
    if s.get("where"):
        z += f" Fundort: {s['where']}."
    if s.get("url"):
        z += f" {s['url']}"
    if s.get("abruf"):
        z += f" (abgerufen {s['abruf']})."
    return z

# ---------- Aussagen sammeln ----------
aussagen = []
def add(person, art, o, text=None):
    if not o:
        return
    aussagen.append({
        "person": person, "art": art, "text": text if text is not None else o.get("t", ""),
        "stufe": o.get("lvl", ""), "stufe_name": LV.get(o.get("lvl", ""), {}).get("label", ""),
        "sicherheit": o.get("sich") or SICH_DEF.get(o.get("lvl", ""), ""),
        "sicherheit_geprueft": bool(o.get("sich")),
        "quellen": o.get("src", []),
        "ns_zeit": bool(o.get("ns")),
    })

for pid, p in P.items():
    if p.get("born"):
        add(pid, "geburt", p["born"], " ".join(x for x in ["geboren", datum(p, p["born"]), ort(p, p["born"])] if x))
    if p.get("died"):
        add(pid, "tod", p["died"], " ".join(x for x in ["gestorben", datum(p, p["died"]), ort(p, p["died"])] if x))
    for f in p.get("facts", []):
        add(pid, "aussage", f)
for e in FA.get("timeline", []):
    add(e.get("p", ""), "zeitleiste", e, f"{e.get('d','')}: {e.get('t','')}")

# ---------- JSON, JSONL, CSV ----------
meta = {
    "schema": "https://dasfamilienarchiv.de/schema/archiv/1.0",
    "titel": BK["titel"],
    "signatur": BK["signatur"],
    "stand": STAND, "erzeugt": datetime.date.today().isoformat(),
    "herausgeber": BK["autor"],
    "lizenz": "Privat. Nur für die Familie; Weitergabe nur mit Zustimmung.",
    "datenschutz": "Lebende nur mit Jahreszahlen, keine Straßenadressen Lebender, Minderjährige nur mit Geburtsjahr.",
    "methode": "Belegstufen und Sicherheit nach dem Skill genealogy-historian (https://github.com/tillheidrich/genealogy-historian).",
}
export = dict(FA)
export["persons"] = {}
for pid, p in P.items():
    q = dict(p)
    for k in ("born", "died"):
        if q.get(k):
            q[k] = dict(q[k]); q[k]["d"] = datum(p, p[k]); q[k]["p"] = ort(p, p[k])
    export["persons"][pid] = q
with open(os.path.join(D, "archiv.json"), "w", encoding="utf-8") as fh:
    json.dump({"meta": meta, "archiv": export}, fh, ensure_ascii=False, indent=1)

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": meta["schema"], "title": "Familienarchiv, Datenformat 1.0",
    "type": "object", "required": ["meta", "archiv"],
    "properties": {"meta": {"type": "object"}, "archiv": {"type": "object", "properties": {
        "levels": {"type": "object", "description": "Belegstufen: Kürzel → {label, long}"},
        "sources": {"type": "array", "items": {"type": "object", "required": ["id", "title"], "properties": {
            "id": {"type": "string"}, "cls": {"type": "string", "description": "P Primär, S abgeleitet, E Erinnerung, I Fundhilfe, K Kontext"},
            "kind": {"type": "string", "description": "Belegstufe der Quelle"}, "title": {"type": "string"}, "detail": {"type": "string"},
            "where": {"type": "string"}, "url": {"type": "string"}, "abruf": {"type": "string"}}}},
        "persons": {"type": "object", "additionalProperties": {"type": "object", "properties": {
            "name": {"type": "string"}, "born": {"$ref": "#/$defs/ereignis"}, "died": {"$ref": "#/$defs/ereignis"},
            "facts": {"type": "array", "items": {"$ref": "#/$defs/aussage"}}}}},
        "couples": {"type": "array"}, "timeline": {"type": "array"}}}},
    "$defs": {
        "ereignis": {"type": "object", "properties": {"d": {"type": "string"}, "p": {"type": "string"}, "lvl": {"type": "string"}, "src": {"type": "array", "items": {"type": "string"}}}},
        "aussage": {"type": "object", "required": ["t", "lvl"], "properties": {"t": {"type": "string"}, "lvl": {"type": "string"},
            "sich": {"enum": ["belegt", "sehr wahrscheinlich", "möglich", "unklar"]}, "src": {"type": "array", "items": {"type": "string"}}}}},
}
with open(os.path.join(D, "archiv.schema.json"), "w", encoding="utf-8") as fh:
    json.dump(schema, fh, ensure_ascii=False, indent=1)

with open(os.path.join(D, "aussagen.jsonl"), "w", encoding="utf-8") as fh:
    for a in aussagen:
        fh.write(json.dumps(a, ensure_ascii=False) + "\n")

def write_csv(name, header, rows):
    with open(os.path.join(D, name), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";"); w.writerow(header); w.writerows(rows)

write_csv("aussagen.csv", ["person", "art", "text", "stufe", "stufe_name", "sicherheit", "sicherheit_geprueft", "quellen"],
          [[a["person"], a["art"], a["text"], a["stufe"], a["stufe_name"], a["sicherheit"], "ja" if a["sicherheit_geprueft"] else "nein", " | ".join(a["quellen"])] for a in aussagen])
write_csv("personen.csv", ["id", "name", "familie", "geboren", "geburtsort", "gestorben", "sterbeort", "lebt"],
          [[pid, p["name"], p.get("fam", ""), datum(p, p.get("born")), ort(p, p.get("born")), datum(p, p.get("died")), ort(p, p.get("died")), "ja" if p.get("living") else ""] for pid, p in P.items()])
write_csv("quellen.csv", ["id", "gruppe", "stufe", "titel", "beschreibung", "fundort", "url", "abgerufen", "zitierform"],
          [[s["id"], s.get("cls", ""), s.get("kind", ""), s["title"], s.get("detail", ""), s.get("where", ""), s.get("url", ""), s.get("abruf", ""), zitat_lang(s)] for s in FA["sources"]])
def couple_m(c):
    m = c.get("m") or {}
    lebt = any(P.get(x, {}).get("living") for x in (c.get("a"), c.get("b")))
    return (year(m.get("d")) if lebt else m.get("d", "")), m.get("lvl", "")
write_csv("familien.csv", ["partner_a", "partner_b", "heirat", "stufe", "kinder"],
          [[c.get("a", ""), c.get("b", ""), *couple_m(c), " | ".join(c.get("kids", []))] for c in FA["couples"]])
R = FA["research"]
write_csv("forschungslog.csv", ["datum", "art", "text", "quellen"], [[e.get("d", ""), e.get("how", ""), e.get("t", ""), " | ".join(e.get("src", []))] for e in R["log"]])
write_csv("negativbefunde.csv", ["datum", "wo", "gesucht", "ergebnis"], [[n.get("d", ""), n.get("where", ""), n.get("q", ""), n.get("r", "")] for n in R["negatives"]])
write_csv("offene-aufgaben.csv", ["status", "aufgabe", "person"], [[n.get("st", ""), n.get("t", ""), n.get("p", "")] for n in R["next"]])

# ---------- GEDCOM ----------
MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
QUAY = {"U": 3, "R": 3, "A": 3, "Z": 2, "B": 2, "F": 1, "E": 1, "L": 1, "H": 0, "O": 0}
ids = list(P.keys()); srcids = list(S.keys())
def gdate(p, d):
    if not d:
        return ""
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", str(d))
    if m and not privat(p):
        return f"{int(m.group(1))} {MON[int(m.group(2))-1]} {m.group(3)}"
    y = year(d)
    return (("ABT " if re.match(r"^(um|ca)", str(d)) else "") + y) if y else ""
def esc_g(v):
    return str(v).replace("\r", " ").replace("\n", " ").replace("@", "@@")

def gedcom(version):
    L = []
    ln = lambda lvl, tag, val="": L.append(f"{lvl} {tag}" + (f" {esc_g(val)}" if val != "" else ""))
    def cite(lvl, src, q):
        for r in src or []:
            sid = str(r).split(" ")[0]
            if sid in S:
                ln(lvl, "SOUR", f"@S{srcids.index(sid)+1}@"); rest = str(r)[len(sid):].strip()
                if rest: ln(lvl+1, "PAGE", rest)
                ln(lvl+1, "QUAY", QUAY.get(q, 0))
            elif str(r).startswith("DFA-JUN-F") and "DFA" in S:
                ln(lvl, "SOUR", f"@S{srcids.index('DFA')+1}@"); ln(lvl+1, "PAGE", r); ln(lvl+1, "QUAY", QUAY.get(q, 0))
    ln(0, "HEAD")
    ln(1, "GEDC"); ln(2, "VERS", "7.0" if version == 7 else "5.5.1")
    if version != 7:
        ln(2, "FORM", "LINEAGE-LINKED"); ln(1, "CHAR", "UTF-8")
    ln(1, "SOUR", "DASFAMILIENARCHIV"); ln(2, "NAME", "Das Familienarchiv, Archivpaket")
    ln(1, "DATE", f"{int(ISO[8:10])} {MON[int(ISO[5:7])-1]} {ISO[:4]}")
    ln(1, "NOTE", BK["titel"] + ". Belegstufe als QUAY (3 Urkunde/Karte, 2 Zeitung/Beschriftung, 1 Familie/Literatur, 0 Vermutung/offen) und als NOTE. Lebende nur mit Jahreszahlen.")
    fam_of = {}
    for i, c in enumerate(FA["couples"]):
        fam_of[i] = f"@F{i+1}@"
    for i, pid in enumerate(ids):
        p = P[pid]; ln(0, f"@I{i+1}@", "INDI") if False else L.append(f"0 @I{i+1}@ INDI")
        nm = p["name"]; parts = nm.split(" "); sur = p.get("fam", parts[-1]).split(" ")[0]
        given = nm.replace(sur, "").strip() if sur in nm else " ".join(parts[:-1])
        ln(1, "NAME", f"{given} /{sur}/")
        for tag, k in (("BIRT", "born"), ("DEAT", "died")):
            o = p.get(k)
            if o:
                ln(1, tag); d = gdate(p, o.get("d"))
                if d: ln(2, "DATE", d)
                if ort(p, o): ln(2, "PLAC", ort(p, o))
                ln(2, "NOTE", f"Belegstufe {o.get('lvl','')}: {LV.get(o.get('lvl',''),{}).get('label','')}; Sicherheit {o.get('sich') or SICH_DEF.get(o.get('lvl',''),'')}")
                cite(2, o.get("src"), o.get("lvl"))
        if p.get("living") and version == 7:
            ln(1, "RESN", "PRIVACY")
        elif p.get("living"):
            ln(1, "RESN", "privacy")
        for f in p.get("facts", [])[:40]:
            ln(1, "NOTE", f"[{f.get('lvl','')}, {f.get('sich') or SICH_DEF.get(f.get('lvl',''),'')}] {f.get('t','')}")
            if version == 7:
                cite(2, f.get("src"), f.get("lvl"))
        for j, c in enumerate(FA["couples"]):
            if pid in (c.get("a"), c.get("b")): ln(1, "FAMS", fam_of[j])
            if pid in c.get("kids", []): ln(1, "FAMC", fam_of[j])
    for j, c in enumerate(FA["couples"]):
        L.append(f"0 {fam_of[j]} FAM")
        if c.get("a") in ids: ln(1, "HUSB", f"@I{ids.index(c['a'])+1}@")
        if c.get("b") in ids: ln(1, "WIFE", f"@I{ids.index(c['b'])+1}@")
        for k in c.get("kids", []):
            if k in ids: ln(1, "CHIL", f"@I{ids.index(k)+1}@")
        m = c.get("m")
        if m:
            lebt = any(P.get(x, {}).get("living") for x in (c.get("a"), c.get("b")))
            ln(1, "MARR"); d = year(m.get("d")) if lebt else gdate({}, m.get("d"))
            if d: ln(2, "DATE", d)
            cite(2, m.get("src"), m.get("lvl"))
        if c.get("prob"): ln(1, "NOTE", c["prob"])
    for i, sid in enumerate(srcids):
        s = S[sid]; L.append(f"0 @S{i+1}@ SOUR"); ln(1, "TITL", s["title"])
        if s.get("where"): ln(1, "PUBL" if version != 7 else "PUBL", s["where"])
        if s.get("url") and version == 7: ln(1, "NOTE", s["url"] + (f" (abgerufen {s['abruf']})" if s.get("abruf") else ""))
        ln(1, "TEXT", s.get("detail", "")[:900])
    ln(0, "TRLR")
    return "\n".join(L) + "\n"

with open(os.path.join(D, "familienarchiv.ged"), "w", encoding="utf-8") as fh:
    fh.write(gedcom(7))
with open(os.path.join(D, "familienarchiv-551.ged"), "w", encoding="utf-8") as fh:
    fh.write(gedcom(551))

# ---------- Buch ----------
# Grundsatz: populärwissenschaftlich. Zuerst die Geschichte und die Bilder, groß;
# die Belege stehen dezent daneben (Buchstabe + Fußnote) und vollständig im Anhang.
e = lambda t: html.escape(str(t or ""))
def fns(src):
    return "".join(f'<span class="fn">{e(zitat(r))}</span>' for r in (src or []))
def mark(o):
    lv = o.get("lvl", "")
    return f'<span class="mk mk-{lv}" title="{e(LV.get(lv,{}).get("label",""))}">{lv}</span>'

CACHE = os.path.join(PUB, "exports", ".bildcache")
os.makedirs(CACHE, exist_ok=True)
def druckbild(pth, max_px=1600):
    """Bild für den Druck: höchstens 1600 px (300 dpi bei rund 13,5 cm), JPEG."""
    from PIL import Image
    out = os.path.join(CACHE, os.path.basename(pth).rsplit(".", 1)[0] + f"_{max_px}.jpg")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(pth):
        im = Image.open(pth).convert("RGB"); im.thumbnail((max_px, max_px)); im.save(out, "JPEG", quality=86, dpi=(300, 300))
    return "file://" + out
def img_path(i, px=1600):
    pth = os.path.join(BDIR, f"{BPRE}{i}.webp")
    return druckbild(pth, px) if os.path.exists(pth) else ""
def caption(i):
    x = FA.get("extra", {}).get(i)
    if x:
        return f"{x.get('cap','')}. {x.get('cite','')}".strip()
    if i.endswith("_Rueckseite"):
        bk = FA.get("backs", {}).get(i[:-11], "")
        return "Rückseite" + (f": „{bk}“" if bk else "")
    fr = FA.get("fronts", {}).get(i, ""); bk = FA.get("backs", {}).get(i, "")
    names = [P[pid]["name"] for pid, p in P.items() if i in (p.get("photos") or [])]
    t = fr or (", ".join(names) if names else "")
    if bk:
        t += (" " if t else "") + f"Rückseite: „{bk}“"
    return t
def ratio(pth):
    from PIL import Image
    with Image.open(pth) as im:
        return im.width / im.height
def fit(pth, mw, mh):
    r = ratio(pth); w = mw; h = w / r
    if h > mh:
        h = mh; w = h * r
    return round(w, 2), round(h, 2)
def foto_pfad(i):
    x = FA.get("extra", {}).get(i)
    if x and (x.get("datei") or x.get("full")):
        q = x["datei"] if x.get("datei") else os.path.join(PUB, x["full"].lstrip("/"))
        return q if os.path.exists(q) else ""
    pth = os.path.join(BDIR, f"{BPRE}{i}.webp")
    return pth if os.path.exists(pth) else ""
def fig_mm(pth, w, h, cap="", sig="", cls="bild", px=2000):
    c = f"<figcaption>{('<span class=sig>' + e(sig) + '</span>') if sig else ''}{e(cap)}</figcaption>" if (cap or sig) else ""
    return f"<figure class='{cls}' style='width:{w}mm'><img src='{druckbild(pth, px)}' style='width:{w}mm;height:{h}mm'>{c}</figure>"
def figure(i, mw=None, mh=None, cls="bild"):
    mw = mw or TW; mh = mh or AH * .7
    pth = foto_pfad(i)
    if not pth:
        return ""
    w, h = fit(pth, mw, mh)
    sig = f"{KURZ}-{i}" if i in FA.get("extra", {}) else f"{KURZ}-F{i.replace('_Rueckseite', ' Rückseite')}"
    return fig_mm(pth, w, h, caption(i), sig, cls)
def paar(ids, Hmax=105, gap=6):
    """Bilder auf gleicher Höhe, zusammen genau so breit wie der Satzspiegel."""
    ps = [foto_pfad(i) for i in ids]
    rs = [ratio(x) for x in ps]
    h = min(Hmax, (TW - gap * (len(ids) - 1)) / sum(rs))
    sg = lambda i: f"{KURZ}-{i}" if i in FA.get("extra", {}) else f"{KURZ}-F{i.replace('_Rueckseite', ' Rückseite')}"
    return "<div class='paar'>" + "".join(fig_mm(x, round(h * r, 2), round(h, 2), caption(i), sg(i)) for x, r, i in zip(ps, rs, ids)) + "</div>"

gen_order = sorted(P.items(), key=lambda kv: (kv[1].get("gen", 0), kv[1].get("side", ""), kv[1]["name"]))
gens = {}
for pid, p in gen_order:
    gens.setdefault(p.get("gen", 0), []).append((pid, p))
GEN_NAME = {int(k): v for k, v in BK["gen_namen"].items()} if BK["gen_namen"] else {-4: "Ururgroßeltern und früher", -3: "Urgroßeltern", -2: "Großeltern", -1: "Eltern", 0: "Die mittlere Generation", 1: "Kinder", 2: "Enkel", 3: "Urenkel"}

parts = []
# Umschlag: Foto randabfallend, darüber ein dunkler Verlauf, unten volle Farbfläche für den Titel
def cover_bild():
    """Foto und Verlauf als ein Bild (300 dpi, mit 3 mm Beschnitt): druckt überall gleich, ohne Transparenz."""
    from PIL import Image
    px_mm = 300 / 25.4
    cw_, ch_ = int((W + 6) * px_mm), int((H + 6) * px_mm)
    im = Image.open(foto_pfad(BK["cover"])).convert("RGB")
    sc = max(cw_ / im.width, ch_ / im.height); im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    oy = int((im.height - ch_) * .08); ox = (im.width - cw_) // 2
    im = im.crop((ox, oy, ox + cw_, oy + ch_))
    base = (30, 60, 62); top = (20, 38, 40)
    ov = Image.new("RGB", im.size, base); mask = Image.new("L", im.size)
    for y in range(ch_):
        f = y / ch_
        if f < .22:
            a = .55 * (1 - f / .22)
        elif f < .42:
            a = 0
        elif f < .66:
            a = min(1, (f - .42) / .24) ** 1.3
        else:
            a = 1
        mask.paste(int(a * 255), (0, y, cw_, y + 1))
    oben = Image.new("RGB", im.size, top)
    im = Image.composite(ov, im, mask)
    out = os.path.join(CACHE, f"cover_{W:g}x{H:g}.jpg"); im.save(out, "JPEG", quality=90, dpi=(300, 300))
    return "file://" + out
COVER_CSS = (f"@page cover {{ background: url('{cover_bild()}') center / {W + 6}mm {H + 6}mm no-repeat; }}" if foto_pfad(BK["cover"]) else "@page cover { background: #1e3c3e; }")
parts.append(f"""<section class="cover"><p class="sig oben">Familienarchiv · {e(BK["signatur"])}</p><div class="feld"><h1>{BK["titel_html"]}</h1>
<p class="unter">{BK["untertitel_html"]}</p></div><p class="hg">{e(BK["hg"])} · {e(STAND[-4:] if STAND[-4:].isdigit() else STAND[:4])}</p></section>""")
parts.append(f'<section class="schmutztitel"><p class="t">{e(BK["titel"])}</p><p class="u">Eine belegte Familiengeschichte</p></section>')
parts.append(f"""<section class="impressum"><p><b>{e(BK["titel"])}. Eine belegte Familiengeschichte.</b> Stand {e(STAND)}.</p>
{BK["impressum_html"]}
<p>Die Daten hinter diesem Buch liegen in offenen Formaten (GEDCOM 7, JSON, CSV) der archivfesten PDF-Ausgabe bei. Kartengrundlage: Natural Earth (gemeinfrei). Satz: Source Serif 4 und Albert Sans (SIL Open Font License). Format {W:g} × {H:g} mm.</p></section>""")
TEILE = [("0", "Die Welt, in der sie lebten", "Karten, Zeitabschnitte und der Stammbaum: der Rahmen für alles, was folgt."),
         ("I", "Die Geschichten", "Was die Familie erzählt und was die Quellen dazu sagen."),
         ("F", "Fakten und Zusammenhänge", "Was wir sicher wissen, was überrascht und wie wir es herausgefunden haben."),
         ("II", "Bilder", "Die Fotos aus den Alben, groß und mit dem, was auf ihren Rückseiten steht."),
         ("III", "Urkunden und Briefe", "Standesamtsregister und Archivpost, mit Abschrift und Erklärung."),
         ("IV", "Die NS-Zeit", "Die Karteikarten der NSDAP-Mitgliederkartei, lesbar und eingeordnet."),
         ("V", "Die Menschen", "Alle Personen nach Generationen, mit Lebensdaten und Belegen."),
         ("VI", "Funde in Zeitungen und Archiven", "Zeitungsmeldungen im Wortlaut, übersetzt und eingeordnet."),
         ("VII", "Zeitleiste", "Zweihundert Jahre in einer Liste."),
         ("A", "Für Genaue", "Belegstufen, Begriffe, Quellen, offene Fragen, Personenregister und das ganze Fotoarchiv.")]
HAT = {"F": bool(FA.get("fakten")), "III": bool(FA.get("docs")), "IV": bool((FA.get("ns") or {}).get("kartei")), "VI": bool((FA.get("presse") or {}).get("items"))}
TEILE = [t for t in TEILE if HAT.get(t[0], True)]
ROEM0 = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
_nr = {k: ROEM0[i] for i, k in enumerate([k for k, _, _ in TEILE if k not in ("0", "A")])}
inh = "".join(f"<li><span class='n'>{'' if n=='0' else ('Anh.' if n=='A' else _nr[n])}</span><span class='t'>{e(t)}</span><a href='#teil-{n}'></a></li>" for n, t, _ in TEILE)
parts.append("<!--INHALT-->")

ROEM = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
NUMMER = {k: ROEM[i] for i, k in enumerate([k for k, _, _ in TEILE if k not in ("0", "A")])}
def teil(n):
    for k, t, z in TEILE:
        if k == n:
            nr = NUMMER.get(n, "")
            extra = K.FOTO_HILFE.replace("class='hinweis'", "class='teilhinweis'") if n == "II" else ""
            return f'<section class="teil" id="teil-{n}"><p class="teilnr">{nr}</p><h2 class="teilh">{e(t)}</h2><p class="teilzeile">{e(z)}</p>{extra}</section>'

# Vorwort und Lesehilfe, kurz
lv_list = "".join(f"<li><span class='mk mk-{k}'>{k}</span> {e(v['label'])}</li>" for k, v in LV.items())
parts.append(f"""<section class="kap vorwort" id="vorwort"><h2>Bevor es losgeht</h2>
{BK["vorwort_html"]}
<p>Wo die Geschichte auf Quellen beruht, steht hinter dem Satz ein kleiner Buchstabe, und unten auf der Seite steht, wo man die Quelle findet. Familienerzählungen sind als solche erkennbar; viele davon ließen sich bestätigen, manche haben sich als anders herausgestellt, und das ist oft die bessere Geschichte.</p>
<ul class="lv-leiste">{lv_list}</ul></section>""")

# Teil 0: Die Welt, in der sie lebten
import kontext as K
ORTE = BK.get("orte") or os.path.join(PUB, "places.js")
PLC = {"list": FA.get("orte", [])} if (FA.get("orte") or not os.path.exists(ORTE)) else json.loads(subprocess.run(["node", "-e", "global.window={};require(process.argv[1]);process.stdout.write(JSON.stringify(window.PLACES))", ORTE], capture_output=True, text=True, check=True).stdout)
parts.append(teil("0"))
ek, ekh, POS = K.europakarte(PLC, BK["regionen"], BK["orte_extra"], BK["karte_bbox"])
dist = ", ".join(f"{n} rund {K.km(POS[a], POS[b]):.0f} km" for a, b, n in BK["entfernungen"] if a in POS and b in POS)
parts.append(f"""<section class='kap karte-s'><h2>Wo sie lebten</h2>{BK["karte_lead_html"]}
<figure class='karte-gross'>{ek}<figcaption>Orte der Familie auf einer Karte mit den Grenzen von heute. {BK["karte_hinweis"]} Luftlinie {dist}. Kartengrundlage Natural Earth; Lage der Orte nach OpenStreetMap, die Orte in der Bretagne ungefähr.</figcaption></figure></section>""")
if BK["revier"]:
    rv0 = BK["revier"] if isinstance(BK["revier"], dict) else {}
    rk, rkh = K.revierkarte(POS, rv0.get("punkte"), rv0.get("orient", []), rv0.get("bbox"), rv0.get("zentrum"), rv0.get("hervor", ""))
    rv = BK["revier"] if isinstance(BK["revier"], dict) else {}
    parts.append(f"""<section class='kap karte-s'><h2>{e(rv.get('titel', 'Die Gegend'))}</h2>{rv.get('lead_html', '')}
<figure class='karte-gross'>{rk}<figcaption>{e(rv.get('cap', 'Orte der Familie. Lage nach OpenStreetMap.'))}</figcaption></figure></section>""")
for root, wer in BK["wurzeln"]:
    parts.append(f"""<section class='kap ahnen'><h2>Die Vorfahren von {wer}</h2><figure class='baum'>{K.ahnentafel(FA, root, 158)}<figcaption>Ahnentafel über vier Generationen; Väter jeweils oben. Durchgezogene Linie: Abstammung durch Urkunde belegt. Gestrichelt: wahrscheinlich, aber noch ohne Urkunde. Leere Felder: noch nicht gefunden, hier kann die Suche weitergehen.</figcaption></figure></section>""")
kinder = [P[k]["name"] + (f" ({K._jahr(P[k].get('born'))})" if K._jahr(P[k].get('born')) else "") for c in FA["couples"] if {c.get("a"), c.get("b")} == {r for r, _ in BK["wurzeln"][:2]} for k in c.get("kids", []) if k in P]
ep = "".join(f"<article class='epoche'><p class='kicker'>{e(z)}</p><h3>{e(t)}</h3><p>{e(x)}</p></article>" for z, t, x in (BK.get("epochen") or K.EPOCHEN))
parts.append(f"""<section class='kap epochen'><h2>{e(BK.get('epochen_titel') or 'Zweihundert Jahre in sieben Abschnitten')}</h2><p class='lead'>Was die Menschen in diesem Buch erlebt haben, hängt an der großen Geschichte: an Grenzen, Kriegen und der Kohle. Diese Seiten geben den Rahmen.</p>{ep}<p class='quelle'>Allgemeiner historischer Rahmen, zusammengestellt für dieses Buch. {e(BK.get('lesetipp') or K.LESETIPP)}</p></section>""")
parts.append(f"""<section class='kap fw-s'><h2>Familie und Welt</h2><p class='lead'>Links, was in der Familie geschah, rechts, was gleichzeitig in der Welt passierte.</p>{K.familie_und_welt(FA, P, BK.get('welt'))}</section>""")

# Teil I: Geschichten, groß bebildert
parts.append(teil("I"))
for st in FA.get("stories", []):
    imgs = list(st.get("images") or [])
    for m in re.findall(r"F(\d{4})", json.dumps(st, ensure_ascii=False)):
        if m not in imgs:
            imgs.append(m)
    imgs = [i for i in imgs if foto_pfad(i)]
    head = ""
    if imgs:
        r0 = ratio(foto_pfad(imgs[0]))
        head = figure(imgs[0], TW, AH * (.47 if r0 >= 1 else .53), "bild auf")
    body = "".join(f"<p>{e(x)}</p>" for x in st.get("body", []))
    rest = imgs[1:]
    more = ""
    while rest:
        grp, rest = rest[:2], rest[2:]
        more += paar(grp, AH * .45) if len(grp) > 1 else figure(grp[0], CW, AH * .52, "bild auf")
    parts.append(f"<article class='story'>{head}<p class='kicker'>{e(st.get('kicker',''))}</p><h3>{e(st['title'])}</h3>{body}{more}<p class='proof'><b>Worauf das beruht</b> {e(st.get('proof',''))}</p></article>")

# Teil: Fakten und Zusammenhänge
if HAT["F"]: parts.append(teil("F"))
fk = {}
for f in FA.get("fakten", []):
    fk.setdefault(f.get("k", "Weiteres"), []).append(f)
for kat, L3 in fk.items():
    karten = "".join(f"<article class='fakt'><p>{e(f.get('t',''))}{mark(f)}{fns(f.get('src'))}</p>{('<p class=wie><b>Wie wir das wissen</b> ' + e(f['how']) + '</p>') if f.get('how') else ''}</article>" for f in L3)
    parts.append(f"<section class='kap fakten'><h2>{e(kat)}</h2>{karten}</section>")

# Teil II: Bilder, groß
used = set()
for st in FA.get("stories", []):
    used.update(st.get("images") or [])
bildfolge = []
for pid, p in gen_order:
    for i in (p.get("photos") or []):
        if i not in used and i not in bildfolge:
            bildfolge.append(i)
for i in FA.get("fronts", {}):
    if i not in used and i not in bildfolge:
        bildfolge.append(i)
parts.append(teil("II"))
tafeln = []
def vollbild(i):
    """Randabfallend, nur wenn das Bild höchstens 5 % vom Seitenformat abweicht."""
    pth = foto_pfad(i); r = ratio(pth)
    w = W + 6; h = w / r
    if h < H + 6:
        h = H + 6; w = h * r
    return (f"<section class='vollbild'><div class='vb' style='width:{W + 6}mm;height:{H + 6}mm'><img src='{druckbild(pth, 2600)}' style='width:{w:.1f}mm;height:{h:.1f}mm;"
            f"margin-left:{(W + 6 - w) / 2:.1f}mm;margin-top:{(H + 6 - h) / 2:.1f}mm'></div><p class='vbcap'><span class='sig'>{KURZ}-F{e(i)}</span> {e(caption(i))}</p></section>")
def doppelseite(i):
    """Querformat über zwei Seiten, nicht beschnitten; die Bildmitte liegt im Bund."""
    pth = foto_pfad(i); r = ratio(pth)
    bw = 2 * W - 2 * MO; bh = bw / r
    if bh > AH - 12:
        bh = AH - 12; bw = bh * r
    top = MT + (AH - 12 - bh) / 2
    links = W - bw / 2
    src = druckbild(pth, 3200)
    seite = lambda off: f"<div class='ds' style='height:{H}mm'><img src='{src}' style='position:absolute;top:{top:.1f}mm;left:{off:.1f}mm;width:{bw:.1f}mm;height:{bh:.1f}mm'></div>"
    cap = f"<p class='dscap' style='top:{top + bh + 3:.1f}mm;left:{MI:.1f}mm;width:{TW:.1f}mm'><span class='sig'>{KURZ}-F{e(i)}</span> {e(caption(i))}</p>"
    return f"<section class='doppel links'>{seite(links)}</section><section class='doppel rechts'>{seite(links - W)}{cap}</section>"
def bildband(liste):
    out, k, seit_ds, seit_vb, wechsel = [], 0, 99, 99, 0
    rr = {i: ratio(foto_pfad(i)) for i in liste}
    while k < len(liste):
        i = liste[k]; r = rr[i]; nxt = liste[k + 1] if k + 1 < len(liste) else None
        if BILDER == "kompakt":
            grp = liste[k:k + 4]
            out.append("<section class='tafelseite vier'>" + "".join(f"<div class='zelle'>{figure(x, (TW - 6) / 2, (AH - 6) / 2 - 14)}</div>" for x in grp) + "</section>"); k += 4; continue
        if r >= 1.3 and seit_ds >= 8:
            out.append(doppelseite(i)); k += 1; seit_ds = 0; seit_vb += 2; continue
        if abs(r - W / H) / (W / H) <= .05 and seit_vb >= 5:
            out.append(vollbild(i)); k += 1; seit_vb = 0; seit_ds += 1; continue
        if r >= 1.15 and nxt and rr[nxt] >= 1.15:
            out.append("<section class='tafelseite zwei'>" + figure(i, TW, (AH - 22) / 2) + figure(nxt, TW, (AH - 22) / 2) + "</section>"); k += 2
        elif r < 1 and nxt and rr[nxt] < 1 and wechsel % 2 == 1:
            hh = min(AH - 24, (TW - 6) / (r + rr[nxt]))
            out.append("<section class='tafelseite'>" + paar([i, nxt], hh) + "</section>"); k += 2
        else:
            out.append("<section class='tafelseite'>" + figure(i, TW, AH - 20) + "</section>"); k += 1
        wechsel += 1; seit_ds += 1; seit_vb += 1
    return "".join(out)
tafeln.append(bildband([i for i in bildfolge if foto_pfad(i)]))
if BK["beispielbilder"]:
    bb = "".join(f"<section class='tafelseite'>{fig_mm(x['datei'], *fit(x['datei'], TW, AH - 30), x['cap'], x.get('sig', ''))}</section>" for x in BK["beispielbilder"])
    tafeln.append(f"<section class='kap' id='k-beispiel'><h2>So sehen Fotos im Buch aus</h2><p class='lead'>{BK.get('beispiel_text', '')}</p></section>{bb}")
gezeigt = set(used) | set(bildfolge)
rest_alle = sorted(k.replace(BPRE, "").rsplit(".", 1)[0] for k in (os.listdir(BDIR) if os.path.isdir(BDIR) else []) if k.startswith(BPRE) and "Rueckseite" not in k)
rest_alle = [i for i in rest_alle if i not in gezeigt]
if rest_alle: tafeln.append(f"<section class='kap' id='k-weitere'><h2>Weitere Fotos aus den Alben</h2><p class='lead'>Die übrigen {len(rest_alle)} Fotos des Bestands, alle groß, damit kein Bild nur als Briefmarke überliefert ist. Wer auf ihnen zu sehen ist, ist noch nicht bestimmt; vielleicht erkennt jemand aus der Familie die Gesichter.</p></section>")
tafeln.append(bildband(rest_alle))
# Rückseiten mit Schrift groß
rs = sorted(k.replace(BPRE, "").rsplit(".", 1)[0] for k in (os.listdir(BDIR) if os.path.isdir(BDIR) else []) if k.startswith(BPRE) and "Rueckseite" in k)
rs = [i for i in rs if i not in used]
if rs:
    tafeln.append("<section class='kap' id='k-rueck'><h2>Die Rückseiten</h2><p class='lead'>Auf den Rückseiten stehen Namen, Grüße, Stempel und Daten. Sie sind oft der einzige Hinweis darauf, wer auf einem Bild zu sehen ist.</p></section>")
    for k in range(0, len(rs), 2):
        tafeln.append("<section class='tafelseite zwei'>" + "".join(figure(i, TW, (AH - 22) / 2) for i in rs[k:k + 2]) + "</section>")
parts.append("".join(tafeln))

# Teil: Dokumente (Urkunden und Briefe mit Scan, Abschrift und Einordnung)
if HAT["III"]:
    parts.append(teil("III"))
    parts.append(K.REGISTER_HILFE)
for dc in FA.get("docs", []):
    pth = dc.get("datei") or os.path.join(PUB, "dokumente", f"{dc.get('img', '')}.webp")
    scan = ""
    if os.path.exists(pth):
        w, h = fit(pth, TW, AH * .85)
        scan = fig_mm(pth, w, h, f"{dc.get('archive','')}", dc['id'], "bild dok", 2600)
    tr = "".join(f"<p>{e(x)}</p>" for x in dc.get("transcript", []))
    asm = "".join(f"<p>{e(x)}</p>" for x in (dc.get("assess") or []))
    parts.append(f"<article class='dokument'><p class='kicker'>{e(dc['id'])} · {e(dc.get('archive',''))}</p><h3>{e(dc['title'])}</h3>{scan}<div class='abschrift'><p class='uk'>Abschrift</p>{tr}<p class='lesung'>{e(dc.get('lesung') or 'Abschrift von der KI (Claude) am Scan gelesen; von einem Menschen noch nicht gegengelesen.')}</p></div><div class='einordnung'><p class='uk'>Was der Eintrag sagt</p>{asm}</div></article>")

# Teil: NS-Zeit mit den Karteikarten, groß und lesbar
N = FA.get("ns", {})
notes = "".join(f"<li>{e(x)}</li>" for x in N.get("notes", []))
if HAT["IV"]:
    parts.append(teil("IV"))
    parts.append(K.ns_einordnung())
if HAT["IV"]: parts.append(f"<section class='kap ns'><h2>Die Karten dieser Familie</h2><ul class='einord'>{notes}</ul><p class='quelle'>Hinweis des SPIEGEL zur Kartei: Die zugrunde liegenden historischen Daten und ihre maschinelle Aufbereitung können unvollständig oder fehlerhaft sein. Suchtreffer und Karteieinträge sollten deshalb nicht ohne weitere Prüfung einer konkreten Person zugeordnet oder als Beleg für politische Überzeugungen oder Handlungen verstanden werden.</p></section>")
for k in N.get("kartei", []):
    scans = ""
    for sc in k.get("scans", []):
        lp = os.path.join(PUB, (sc.get("lokal") or "").lstrip("/"))
        if sc.get("lokal") and os.path.exists(lp):
            w, h = fit(lp, TW, AH * .47)
            scans += fig_mm(lp, w, h, f"Bundesarchiv R 9361, Scan: DER SPIEGEL, abgerufen {sc.get('abruf','')}. {sc.get('url','')}", sc.get('art',''), "bild karte", 2400)
    z = k.get("zuordnung") or {}
    parts.append(f"""<article class='kartei'><p class='kicker'>NSDAP-Mitgliederkartei</p><h3>{e(k['name'])}</h3>{scans}
<table class='kd'><tr><td>Geboren</td><td>{e(k.get('geb',''))}</td></tr><tr><td>Beruf</td><td>{e(k.get('beruf',''))}</td></tr><tr><td>Wohnort</td><td>{e(k.get('wohn',''))}</td></tr><tr><td>Antrag</td><td>{e(k.get('antrag') or 'nicht vermerkt')}</td></tr><tr><td>Aufnahme</td><td>{e(k.get('aufn',''))}, mit {e(k.get('alter',''))} Jahren</td></tr><tr><td>Mitgliedsnummer</td><td>{e(k.get('nr',''))}</td></tr></table>
<p>{e(k.get('ein',''))}</p>
<p class='zv'><b>Zuordnung: {e(z.get('sich',''))}.</b> {e(z.get('grund',''))} Was passt: {e(z.get('merkmale',''))}. Was dagegen spricht: {e(z.get('konflikte',''))}.</p></article>""")

# Teil III: Menschen
parts.append(teil("V"))
for g in sorted(gens):
    parts.append(f'<section class="kap gen"><h2>{e(GEN_NAME.get(g, f"Generation {g}"))}</h2>')
    for pid, p in gens[g]:
        if privat(p) and not p.get("facts"):
            continue
        lines = []
        for k, lab in (("born", "geboren"), ("died", "gestorben")):
            o = p.get(k)
            if o:
                lines.append(f"<span class='ev'>{lab} {e(datum(p, o))}{', ' + e(ort(p, o)) if ort(p, o) else ''}{mark(o)}{fns(o.get('src'))}</span>")
        facts = "".join(f"<p class='fa'>{e(f.get('t',''))}{mark(f)}{fns(f.get('src'))}</p>" for f in p.get("facts", []))
        pic = ""
        if p.get("av") and foto_pfad(p["av"]):
            w, h = fit(foto_pfad(p["av"]), 40, 52)
            pic = fig_mm(foto_pfad(p["av"]), w, h, "", f"F{p['av']}", "bild av", 900)
        parts.append(f"<article class='person' id='p-{pid}'>{pic}<h3>{e(p['name'])}</h3><p class='leben'>{' · '.join(lines)}</p>{('<p class=alt>' + e(p['alt']) + '</p>') if p.get('alt') else ''}{facts}</article>")
    parts.append("</section>")

# Teil IV: Funde
if HAT["VI"]: parts.append(teil("VI"))
parts.append('<section class="funde">')
for it in (FA.get("presse") or {}).get("items", []):
    figs = ""
    for im in [it.get("img"), it.get("img2")]:
        if not im:
            continue
        pth = os.path.join(PUB, im.lstrip("/")) if im.startswith("/") else os.path.join(PUB, "zeitung", f"{im}.webp")
        if os.path.exists(pth):
            w, h = fit(pth, TW, AH * .64)
            figs += fig_mm(pth, w, h, "", "", "bild ausschnitt", 2400)
    parts.append(f"<article class='fund'><p class='kicker'>{e(it.get('d',''))} · {e(it.get('paper',''))}</p><h3>{e(it.get('h',''))}</h3>{figs}<p class='wl'>Wortlaut</p><blockquote>{e(it.get('t',''))}</blockquote><p class='wl'>Auf Deutsch und eingeordnet</p><p>{e(it.get('m',''))}</p><p class='quelle'>{e(it.get('paper',''))}, {e(it.get('d',''))}. {e(it.get('url',''))}</p></article>")
parts.append("</section>")

# Teil V: Zeitleiste
rows = "".join(f"<tr><td class='j'>{e(t.get('d',''))}</td><td>{e(t.get('t',''))}{mark(t)}</td></tr>" for t in FA.get("timeline", []))
parts.append(teil("VII")); parts.append(f'<section class="kap zeitl"><table class="zl">{rows}</table></section>')

# Anhang
lv_rows = "".join(f"<tr><td><span class='mk mk-{k}'>{k}</span></td><td><b>{e(v['label'])}</b></td><td>{e(v['long'])}</td><td>{e(SICH_DEF.get(k,''))}</td></tr>" for k, v in LV.items())
parts.append(teil("A"))
parts.append(f"""<section class="kap" id="lesehilfe"><h2>Belegstufen und Sicherheit</h2>
<p>Jede Angabe trägt eine Belegstufe. In den Daten steht zu jeder Angabe zusätzlich eine Sicherheit (belegt, sehr wahrscheinlich, möglich, unklar); wo sie nicht einzeln geprüft ist, gilt der Richtwert in der letzten Spalte.</p>
<table class="stufen"><tr><th></th><th>Stufe</th><th>Bedeutung</th><th>Richtwert</th></tr>{lv_rows}</table></section>""")
neg = "".join(f"<li><b>{e(n.get('where',''))}</b>, {e(n.get('d',''))}: {e(n.get('q',''))}. {e(n.get('r',''))}</li>" for n in R["negatives"])
log = "".join(f"<li><b>{e(l.get('d',''))}, {e(l.get('how',''))}:</b> {e(l.get('t',''))}</li>" for l in R["log"])
nxt = "".join(f"<li><b>{e(n.get('st',''))}:</b> {e(n.get('t',''))}</li>" for n in R["next"])
qs = "".join(f"<li>{e(q.get('q',''))}</li>" for q in FA.get("questions", []))
parts.append(f"""<section class="kap" id="forschung"><h2>Wie es weitergehen kann</h2>
<h3>Offene Aufgaben</h3><ul class="klein">{nxt}</ul>
<h3>Fragen an die Familie</h3><ul class="klein">{qs}</ul>
<h3>Wo schon gesucht wurde</h3><ul class="klein">{neg}</ul>
<h3>Forschungslog</h3><ul class="klein">{log}</ul></section>""")
glo = (FA.get("presse") or {}).get("glossar", {})
gl_html = "".join(f"<dt>{e(v['t'])}</dt><dd>{e(v['d'])}</dd>" for k2, v in sorted(glo.items(), key=lambda kv: kv[1]['t'].lower()))
parts.append(f'<section class="kap" id="glossar"><h2>Begriffe</h2><p>Wörter aus Urkunden, Zeitungen und Akten, die heute nicht mehr geläufig sind.</p><dl class="glossar">{gl_html}</dl></section>')
groups = [("P", "Primärquellen"), ("S", "Abgeleitete Quellen"), ("E", "Erinnerungen"), ("I", "Fundhilfen"), ("K", "Kontext und Literatur")]
qparts = []
for c, h in groups:
    L2 = [s for s in FA["sources"] if (s.get("cls") or "K") == c]
    if L2:
        qparts.append(f"<h3>{h}</h3><ol class='qv'>" + "".join(f"<li><b>{e(s['id'])}</b> {e(zitat_lang(s))}</li>" for s in L2) + "</ol>")
parts.append(f'<section class="kap" id="quellen"><h2>Quellen</h2>{"".join(qparts)}</section>')

# Fotoarchiv vollständig als Übersicht
alle = sorted(k.replace(BPRE, "").rsplit(".", 1)[0] for k in (os.listdir(BDIR) if os.path.isdir(BDIR) else []) if k.startswith(BPRE) and "Rueckseite" not in k)
thumbs = "".join(f"<figure class='th'><img src='{img_path(i, 420)}'><figcaption>F{e(i)}</figcaption></figure>" for i in alle)
if alle: parts.append(f'<section class="kap" id="fotoarchiv"><h2>Das ganze Fotoarchiv</h2><p>Alle {len(alle)} Fotos des Bestands mit ihrer Signatur. Die Originale liegen in der Familie, die Scans in der digitalen Fassung.</p><div class="kontakt">{thumbs}</div></section>')

reg = "".join(f"<li><a href='#p-{pid}'>{e(p['name'])}</a> <a class='pg' href='#p-{pid}'></a></li>" for pid, p in sorted(P.items(), key=lambda kv: kv[1]['name'].split(' ')[-1] + kv[1]['name']) if not (privat(p) and not p.get('facts')))
n_fotos = len([k for k in (os.listdir(BDIR) if os.path.isdir(BDIR) else []) if k.startswith(BPRE) and "Rueckseite" not in k])
n_rueck = len([k for k in (os.listdir(BDIR) if os.path.isdir(BDIR) else []) if "Rueckseite" in k])
parts.append(f"""<section class="kap" id="entstehung"><h2>Wie dieses Buch entstand</h2>
<p class="lead">Wer dieses Buch in hundert oder zweihundert Jahren liest, soll wissen, wer was dazu beigetragen hat, mit welchen Werkzeugen es gemacht wurde und wo seine Schwächen liegen.</p>
<h3>Was die Familie beigetragen hat</h3>
{BK["familie_html"]}
<h3>Was eine KI beigetragen hat</h3>
<p>Bei Recherche, Text und Satz half {e(BK['ki_zeitraum'])} {e(BK['ki_name'])}, in der Fassung „{e(BK['ki_modell'])}“. Für spätere Leser: Ein solches Programm, damals „großes Sprachmodell“ oder „Künstliche Intelligenz“ (KI) genannt, hat aus sehr vielen Texten gelernt, Sprache zu verstehen und zu schreiben. Es kann Handschriften und alte Zeitungen lesen, Französisch und Polnisch übersetzen, in Online-Archiven suchen und Computerprogramme schreiben. Es arbeitet schnell, kann sich aber irren und, wenn man es nicht kontrolliert, Dinge behaupten, die nicht stimmen. Deshalb gilt in diesem Buch: Jede Aussage nennt ihre Quelle, und wo die KI eine Handschrift gelesen hat und noch kein Mensch die Lesung geprüft hat, steht das ausdrücklich dabei.</p>
{BK["ki_html"]}
<h3>Wie es gemacht ist</h3>
<p>Das Buch ist nicht von Hand gesetzt, sondern aus einer Datensammlung erzeugt: jede Person, jede Aussage, jede Quelle ein Eintrag. Daraus entstehen mit einem Befehl die Website, dieses Buch in beliebigem Format und die Datendateien im Anhang. Satzprogramm: WeasyPrint (Python); Schriften Source Serif 4 und Albert Sans; Karten aus Natural Earth und OpenStreetMap. Dieses Exemplar: Format {W:g} × {H:g} mm, Stand {e(STAND)}.</p>
<h3>Was noch offen ist</h3>
<p>Die Abschriften der Handschriften sind noch nicht vollständig von Menschen gegengelesen. Manche Zuordnungen von Fotos zu Personen beruhen auf Erinnerung und sind als solche gekennzeichnet. Die Liste „Wie es weitergehen kann“ nennt, wo die Suche weitergehen kann.</p></section>""")
parts.append(f'<section class="kap" id="register"><h2>Personen</h2><ul class="reg">{reg}</ul></section>')
parts.append(f"""<section class="kap" id="daten"><h2>Zu den Daten</h2>
<p>Dieses Buch ist aus einer Datensammlung gesetzt. Sie liegt der archivfesten PDF-Ausgabe (PDF/A-3) als Anhang bei und lässt sich mit jedem PDF-Programm herauslösen. Die Formate sind offen und ohne Spezialprogramm lesbar:</p>
<ul><li><b>familienarchiv.ged</b>: Stammbaum als GEDCOM 7.0, dazu GEDCOM 5.5.1 für ältere Programme. Öffnen mit Gramps, Ancestris oder jedem Stammbaumprogramm.</li>
<li><b>archiv.json</b> mit <b>archiv.schema.json</b>: alle Daten vollständig, mit Beschreibung der Felder.</li>
<li><b>aussagen.csv / aussagen.jsonl</b>: jede Aussage eine Zeile, mit Belegstufe, Sicherheit und Quellen.</li>
<li><b>personen.csv, familien.csv, quellen.csv, forschungslog.csv, negativbefunde.csv, offene-aufgaben.csv</b>.</li></ul>
<p>Die Fotos liegen als Bilddateien mit der Signatur im Dateinamen ({BPRE}0001 gehört zu {KURZ}-F0001). Für die Langzeitsicherung: dieses Buch gedruckt, die PDF/A-Datei und die Bilder auf zwei Datenträgern an zwei Orten, alle paar Jahre umkopiert.</p>
<h3>Damit es bleibt</h3>
<p>Gedruckte Bücher überdauern am längsten, wenn es mehrere davon an verschiedenen Orten gibt. Ein Exemplar gehört in jeden Zweig der Familie, eines in das Archiv der Heimatgemeinde, eines an einen genealogischen Verein der Region und eines an die Deutsche Zentralstelle für Genealogie in Leipzig, die Familiengeschichten sammelt. Vorher klären, was davon öffentlich sein darf; die Angaben über Lebende lassen sich für solche Exemplare weglassen.</p>
<h3>Diese Ausgabe</h3>
<p>Dies ist die Ausgabe vom {e(STAND)}. Sie ist nicht die letzte: Wer einen Fehler findet, ein Gesicht erkennt oder ein Foto beisteuern kann, meldet sich bei der Familie; die nächste Ausgabe wird aus denselben Daten neu gesetzt und trägt ein neues Datum.</p></section>""")

parts.append(f"""<section class="rueck">{BK["rueck_html"]}<p class="hg">Familienarchiv {e(BK["titel"].replace("Familie ", ""))} · {e(BK["signatur"])} · Stand {e(STAND)}</p></section>""")
# Inhaltsverzeichnis aus den Kapiteln erzeugen
body = "".join(parts)
zaehler = [0]
def _id(m):
    tag, attrs = m.group(1), m.group(2)
    if "id=" in attrs:
        return m.group(0)
    zaehler[0] += 1
    return f"<{tag}{attrs} id='c{zaehler[0]}'>"
body = re.sub(r"<(section|article)((?:\s+class=(?:'|\")(?:[^'\"]*\b(?:kap|story|dokument|kartei)\b[^'\"]*)(?:'|\")))>", _id, body)
toc, aktuell = [], None
for m in re.finditer(r"<(?:section|article)[^>]*class=(?:'|\")([^'\"]*)(?:'|\")[^>]*id=(?:'|\")([^'\"]+)(?:'|\")[^>]*>(.*?)</h[23]>", body, re.S):
    cls, cid, inner = m.groups()
    h = re.sub(r"<[^>]+>", " ", inner.split("<h2", 1)[-1].split("<h3", 1)[-1])
    h = re.sub(r"\s+", " ", h.split(">", 1)[-1]).strip()
    if "teil" in cls.split():
        aktuell = [cid, h, []]; toc.append(aktuell)
    elif aktuell is not None and h and "fund" not in cls and "person" not in cls:
        aktuell[2].append((cid, h))
def _nr(cid):
    k = cid.replace("teil-", "")
    return "Anhang" if k == "A" else NUMMER.get(k, "")
tl = "".join(f"<li class='tt'><span class='n'>{_nr(c)}</span><span class='t'>{h}</span><a href='#{c}'></a></li>" + "".join(f"<li class='tk'><span class='n'></span><span class='t'>{hh}</span><a href='#{cc}'></a></li>" for cc, hh in kids) for c, h, kids in toc)
body = re.sub(r"width='154mm' height='([\d.]+)mm'", lambda m: f"width='{TW}mm' height='{float(m.group(1)) * TW / 154:.1f}mm'", body)
body = body.replace("<!--INHALT-->", f'<section class="inhalt"><h2>Inhalt</h2><ol><li class="tt"><span class="n"></span><span class="t">Bevor es losgeht</span><a href="#vorwort"></a></li>{tl}</ol></section>', 1)
css = open(os.path.join(HERE, "buch.css"), encoding="utf-8").read()
for a_, b_ in [("size: 200mm 260mm", f"size: {W}mm {H}mm"), ("margin: 22mm 22mm 26mm 24mm", f"margin: {MT}mm {MO}mm {MB}mm {MI}mm"),
               ("margin-left: 22mm; margin-right: 24mm", f"margin-left: {MO}mm; margin-right: {MI}mm"), ("154mm", f"{TW}mm"), ("124mm", f"{CW}mm"),
               ("260mm", f"{H}mm"), ("206mm", f"{AH - 6}mm"), ("74mm", f"{(TW - 6) / 2:.1f}mm"), ("101mm", f"{(AH - 6) / 2 - 2:.1f}mm"), ("font-size: 10.8pt", f"font-size: {FS}pt")]:
    css = css.replace(a_, b_).replace("{FONTS}", "file://" + os.path.join(HERE, "fonts")) + COVER_CSS
import sprachen
body = sprachen.uebersetze(body, SPRACHE)
doc = f"""<!doctype html><html lang="{SPRACHE}"><head><meta charset="utf-8"><title>{e(BK["titel"])}</title>
<meta name="author" content="{e(BK["autor"])}"><meta name="description" content="Belegte Familiengeschichte, Stand {e(STAND)}"><meta name="keywords" content="Familiengeschichte">
<style>{css}</style></head><body>{body}</body></html>"""
with open(os.path.join(B, "buch.html"), "w", encoding="utf-8") as fh:
    fh.write(doc)

# ---------- LIESMICH, RO-Crate, Prüfsummen ----------
liesmich = f"""# {BK["titel"]}, Archivpaket {STAND}

Dieses Verzeichnis ist die dauerhafte Fassung des Familienarchivs. Es braucht keine Website und kein Spezialprogramm.

- `buch/buch-druck-pdfx4.pdf`: druckfertiges Buch im gewählten Format (Standard 200 × 260 mm), mit 3 mm Beschnitt (ohne Schnittmarken, wie die meisten Druckereien es wünschen), PDF/X-4. So an eine Druckerei geben; Papier und Bindung mit der Druckerei abstimmen.
- `buch/buch-archiv-pdfa3.pdf`: dasselbe Buch als PDF/A-3b für die Langzeitarchivierung. Alle Daten aus `daten/` sind darin als Anhang eingebettet.
- `buch/buch.html`: Quelltext des Buchs.
- `bearbeitbar/`: das Buch als OpenDocument (`buch.odt`, öffnet in LibreOffice und Word) und als Markdown (`buch.md`) mit allen Bildern im Ordner `bilder/`. Für freie Änderungen an Text und Bildern. Wer dauerhaft ergänzen will, ändert besser die Daten und baut neu, dann bleiben Website, Buch und Daten gleich.
- `daten/`: alle Daten in offenen Formaten (GEDCOM 7.0 und 5.5.1, JSON mit Schema, JSONL, CSV mit Semikolon, UTF-8).
- `ro-crate-metadata.json`: Beschreibung des Pakets nach RO-Crate 1.1 (JSON-LD), damit Programme und Archive den Inhalt erkennen.
- `SHA256SUMS.txt`: Prüfsummen. Mit `sha256sum -c SHA256SUMS.txt` lässt sich prüfen, ob eine Kopie unverändert ist.

Neu erzeugen: `python3 scripts/paket/build.py` im Repository des Archivs. Optionen:

- `--format A4|A5|B5|17x24|200x260|21x28|magazin|quadrat|letter|7x10|6x9|8x10` oder frei, z. B. `--format 165x235` (Millimeter). Ränder, Satzspiegel, Bilder, Karten und Schriftgröße passen sich an.
- `--bilder gross` (Standard, Bildband mit Doppelseiten, Vollbildern und Paaren) oder `--bilder kompakt` (vier Fotos je Seite, weniger Seiten).
- `--sprache de|en`: Sprache der festen Buchtexte; zusammen mit `--daten data.en.js` (übersetzte Datendatei) entsteht eine fremdsprachige Ausgabe.
- `--ohne-pdf`: nur Daten und HTML, schneller zum Prüfen.

Datenschutz: Lebende Personen nur mit Jahreszahlen, keine Anschriften Lebender. Privat, nur für die Familie.
"""
with open(os.path.join(OUT, "LIESMICH.md"), "w", encoding="utf-8") as fh:
    fh.write(liesmich)

def build_pdfs():
    import weasyprint
    from weasyprint import Attachment
    html_obj = weasyprint.HTML(filename=os.path.join(B, "buch.html"), base_url=ROOT)
    druck_css = weasyprint.CSS(string="@page { bleed: 3mm; }")
    html_obj.write_pdf(os.path.join(B, "buch-druck-pdfx4.pdf"), stylesheets=[druck_css], pdf_variant="pdf/x-4")
    atts = [Attachment(filename=os.path.join(D, f), description=f) for f in sorted(os.listdir(D))]
    weasyprint.HTML(filename=os.path.join(B, "buch.html"), base_url=ROOT).write_pdf(os.path.join(B, "buch-archiv-pdfa3.pdf"), pdf_variant="pdf/a-3b", attachments=atts)

if "--ohne-pdf" not in sys.argv:
    build_pdfs()

# Bearbeitbare Fassung: OpenDocument (LibreOffice, Word) und Markdown mit Bildordner
BE = os.path.join(OUT, "bearbeitbar"); os.makedirs(os.path.join(BE, "bilder"), exist_ok=True)
plain = doc
for src in sorted(set(re.findall(r"src='file://([^']+)'", doc))):
    ziel = os.path.join(BE, "bilder", os.path.basename(src))
    if not os.path.exists(ziel):
        shutil.copy(src, ziel)
    plain = plain.replace(f"file://{src}", f"bilder/{os.path.basename(src)}")
plain = re.sub(r"<style>.*?</style>", "", plain, flags=re.S)
plain = re.sub(r"<svg.*?</svg>", "<p><i>[Karte oder Stammbaum: siehe PDF]</i></p>", plain, flags=re.S)
with open(os.path.join(BE, "buch-einfach.html"), "w", encoding="utf-8") as fh:
    fh.write(plain)
for ziel, fmt in (("buch.odt", "odt"), ("buch.md", "gfm")):
    subprocess.run(["pandoc", "buch-einfach.html", "-f", "html", "-t", fmt, "-o", ziel, "--resource-path", BE], cwd=BE, check=False)
os.remove(os.path.join(BE, "buch-einfach.html"))

files = []
for dp, _, fnames in os.walk(OUT):
    for f in fnames:
        files.append(os.path.relpath(os.path.join(dp, f), OUT))
crate = {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": [
    {"@id": "ro-crate-metadata.json", "@type": "CreativeWork", "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}, "about": {"@id": "./"}},
    {"@id": "./", "@type": "Dataset", "name": meta["titel"], "identifier": meta["signatur"], "datePublished": meta["erzeugt"],
     "description": "Belegtes Familienarchiv mit Stammbaum, Quellen, Belegstufen, Forschungslog und Buchfassung.",
     "author": {"@id": "#till"}, "license": meta["lizenz"], "hasPart": [{"@id": f} for f in sorted(files)]},
    {"@id": "#till", "@type": "Person", "name": BK["autor"]},
] + [{"@id": f, "@type": "File", "encodingFormat": {".json": "application/json", ".jsonl": "application/jsonl", ".csv": "text/csv", ".ged": "application/x-gedcom",
      ".pdf": "application/pdf", ".html": "text/html", ".md": "text/markdown"}.get(os.path.splitext(f)[1], "application/octet-stream")} for f in sorted(files)]}
with open(os.path.join(OUT, "ro-crate-metadata.json"), "w", encoding="utf-8") as fh:
    json.dump(crate, fh, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "SHA256SUMS.txt"), "w") as fh:
    for f in sorted(files + ["ro-crate-metadata.json"]):
        h = hashlib.sha256(open(os.path.join(OUT, f), "rb").read()).hexdigest()
        fh.write(f"{h}  {f}\n")
print(OUT)
