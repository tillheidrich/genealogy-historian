#!/usr/bin/env python3
# Beispiel aus dem Familienarchiv Junker. Passe Pfade und Datenmodell an dein Archiv an.
# Example from a real archive: adapt paths and data model.
"""Archivpaket für das Familienarchiv Junker bauen.

Erzeugt aus public/data.js ein dauerhaftes Paket in exports/paket-<Stand>/:
  daten/   archiv.json (+ Schema), aussagen.jsonl/.csv, personen.csv, quellen.csv,
           familien.csv, forschungslog.csv, negativbefunde.csv, offene-aufgaben.csv,
           familienarchiv-junker.ged (GEDCOM 7.0), familienarchiv-junker-551.ged (GEDCOM 5.5.1)
  buch/    buch.html, buch-druck-pdfx4.pdf (170 x 240 mm, 3 mm Beschnitt, Schnittmarken),
           buch-archiv-pdfa3.pdf (PDF/A-3b, alle Daten als Anhang eingebettet)
  LIESMICH.md, ro-crate-metadata.json, SHA256SUMS.txt

Aufruf:  python3 scripts/paket/build.py [--ohne-pdf]
Regeln:  Lebende nur mit Jahreszahlen, keine Straßenadressen Lebender, Minderjährige nur Geburtsjahr.
         Das Skript liest nur; es überschreibt kein bestehendes Paket.
"""
import csv, hashlib, html, json, os, re, shutil, subprocess, sys, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PUB = os.path.join(ROOT, "public")
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- Daten laden ----------
raw = subprocess.run(["node", "-e", "global.window={};require(process.argv[1]);process.stdout.write(JSON.stringify(window.FA))", os.path.join(PUB, "data.js")],
                     capture_output=True, text=True, check=True).stdout
FA = json.loads(raw)
STAND = FA["stand"]  # TT.MM.JJJJ
ISO = "-".join(reversed(STAND.split(".")))
OUT = os.path.join(ROOT, "exports", f"paket-{ISO}")
if os.path.exists(OUT):
    n = 2
    while os.path.exists(f"{OUT}-{n}"):
        n += 1
    OUT = f"{OUT}-{n}"
D = os.path.join(OUT, "daten"); B = os.path.join(OUT, "buch")
os.makedirs(D); os.makedirs(B)

P = FA["persons"]; S = {s["id"]: s for s in FA["sources"]}
LV = FA["levels"]
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
    m = re.match(r"^DFA-JUN-F(\d{4})(.*)$", r)
    if m:
        fr = FA.get("fronts", {}).get(m.group(1), ""); bk = FA.get("backs", {}).get(m.group(1), "")
        t = f"Familienarchiv Junker (Privatbesitz), Foto DFA-JUN-F{m.group(1)}{m.group(2)}"
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
    "titel": "Familienarchiv Junker und Rückert",
    "signatur": "DFA-JUN-03",
    "stand": STAND, "erzeugt": datetime.date.today().isoformat(),
    "herausgeber": "Till Heidrich, Heidrich Digital (dasfamilienarchiv.de)",
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
    ln(1, "NOTE", "Familienarchiv Junker und Rückert. Belegstufe als QUAY (3 Urkunde/Karte, 2 Zeitung/Beschriftung, 1 Familie/Literatur, 0 Vermutung/offen) und als NOTE. Lebende nur mit Jahreszahlen.")
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

with open(os.path.join(D, "familienarchiv-junker.ged"), "w", encoding="utf-8") as fh:
    fh.write(gedcom(7))
with open(os.path.join(D, "familienarchiv-junker-551.ged"), "w", encoding="utf-8") as fh:
    fh.write(gedcom(551))

# ---------- Buch ----------
e = lambda t: html.escape(str(t or ""))
fn_counter = [0]
def fns(src):
    out = []
    for r in src or []:
        out.append(f'<span class="fn">{e(zitat(r))}</span>')
    return "".join(out)
def mark(o):
    lv = o.get("lvl", ""); si = o.get("sich") or SICH_DEF.get(lv, "")
    return f'<span class="mk mk-{lv}">{lv}</span><span class="si">{e(si)}{"" if o.get("sich") else "*"}</span>'

CACHE = os.path.join(ROOT, "exports", ".bildcache")
os.makedirs(CACHE, exist_ok=True)
def druckbild(pth, max_px=1400):
    """Bild für den Druck: höchstens 1400 px (reicht für 300 dpi bei rund 12 cm), JPEG, sRGB."""
    from PIL import Image
    out = os.path.join(CACHE, os.path.basename(pth).rsplit(".", 1)[0] + ".jpg")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(pth):
        im = Image.open(pth).convert("RGB"); im.thumbnail((max_px, max_px)); im.save(out, "JPEG", quality=88, dpi=(300, 300))
    return "file://" + out
def img_path(i):
    pth = os.path.join(PUB, "bilder", f"Junker_{i}.webp")
    return druckbild(pth) if os.path.exists(pth) else ""

gen_order = sorted(P.items(), key=lambda kv: (kv[1].get("gen", 0), kv[1].get("side", ""), kv[1]["name"]))
gens = {}
for pid, p in gen_order:
    gens.setdefault(p.get("gen", 0), []).append((pid, p))
GEN_NAME = {-4: "Ururgroßeltern der Bezugsgeneration und früher", -3: "Urgroßeltern der Bezugsgeneration", -2: "Großeltern der Bezugsgeneration",
            -1: "Eltern der Bezugsgeneration", 0: "Generation 0", 1: "Kinder der Bezugsgeneration", 2: "Enkel", 3: "Urenkel"}

parts = []
parts.append(f"""<section class="titel"><p class="sig">DFA · JUN · 03</p><h1>Familie Junker<br>und Rückert</h1>
<p class="unter">Ein belegtes Familienarchiv<br>1817 bis heute</p><p class="stand">Stand {e(STAND)}</p>
<p class="hg">Zusammengestellt von Till Heidrich<br>Das Familienarchiv · Heidrich Digital</p></section>""")
parts.append(f"""<section class="impressum"><p><b>Familie Junker und Rückert. Ein belegtes Familienarchiv.</b> Stand {e(STAND)}.</p>
<p>Zusammengestellt von [Name], mit Erinnerungen von [Namen der Zeitzeugen]. Recherche und Satz mit Unterstützung einer KI (Claude); jede Aussage wurde mit einer Quelle und einer Belegstufe versehen. Wo eine Lesung von der KI stammt und noch nicht von einem Menschen geprüft ist, steht das dabei.</p>
<p>Privatdruck für die Familie. Fotos und Dokumente aus Familienbesitz. Archivscans mit Angabe der haltenden Stelle; NSDAP-Kartei: Bundesarchiv R 9361, Scans über DER SPIEGEL; Rotkreuz-Karten: Archiv des IKRK, Genf.</p>
<p>Lebende Personen erscheinen nur mit Jahreszahlen und ohne Anschrift.</p>
<p>Dieses Buch hat eine digitale Fassung mit denselben Daten in offenen Formaten (JSON, CSV, GEDCOM 7). Sie sind in der archivfesten PDF-Ausgabe als Anhang eingebettet. Wie man sie öffnet, steht im Anhang „Zu den Daten“.</p>
<p>Satz: Source Serif 4 und Albert Sans (SIL Open Font License).</p></section>""")

# Lesehilfe
lv_rows = "".join(f"<tr><td><span class='mk mk-{k}'>{k}</span></td><td><b>{e(v['label'])}</b></td><td>{e(v['long'])}</td></tr>" for k, v in LV.items())
parts.append(f"""<section class="kap" id="lesehilfe"><h2>Wie man dieses Buch liest</h2>
<p>Jede Angabe trägt am Ende einen Buchstaben, die Belegstufe. Er sagt, worauf die Angabe beruht. Dahinter steht die Sicherheit: belegt, sehr wahrscheinlich, möglich oder unklar. Ein Sternchen heißt, dass die Sicherheit nach der Belegstufe vergeben und noch nicht einzeln geprüft ist. Die Fußnoten nennen die Quelle so, dass man sie wiederfinden kann.</p>
<table class="stufen">{lv_rows}</table>
<p>Was sich nicht klären ließ, steht als offene Frage im Buch. Familienerzählungen sind als solche gekennzeichnet und dort, wo es möglich war, an Quellen geprüft.</p></section>""")

# Personen
for g in sorted(gens):
    parts.append(f'<section class="kap gen"><h2>{e(GEN_NAME.get(g, f"Generation {g}"))}</h2>')
    for pid, p in gens[g]:
        if privat(p) and not p.get("facts"):
            continue
        lines = []
        for k, lab in (("born", "Geboren"), ("died", "Gestorben")):
            o = p.get(k)
            if o:
                lines.append(f"<p class='ev'><b>{lab}</b> {e(datum(p, o))}{', ' + e(ort(p, o)) if ort(p, o) else ''} {mark(o)}{fns(o.get('src'))}</p>")
        facts = "".join(f"<p class='fa'>{e(f.get('t',''))} {mark(f)}{fns(f.get('src'))}</p>" for f in p.get("facts", []))
        pic = ""
        if p.get("av") and img_path(p["av"]):
            pic = f"<figure class='av'><img src='{img_path(p['av'])}'><figcaption>DFA-JUN-F{e(p['av'])}</figcaption></figure>"
        parts.append(f"<article class='person' id='p-{pid}'><h3>{e(p['name'])}</h3>{('<p class=alt>' + e(p['alt']) + '</p>') if p.get('alt') else ''}{pic}{''.join(lines)}{facts}</article>")
    parts.append("</section>")

# Geschichten
parts.append('<section class="kap" id="geschichten"><h2>Geschichten</h2>')
for st in FA.get("stories", []):
    body = "".join(f"<p>{e(x)}</p>" for x in st.get("body", []))
    imgs = "".join(f"<figure><img src='{img_path(i)}'><figcaption>DFA-JUN-F{e(i)}</figcaption></figure>" for i in (st.get("images") or [])[:2] if img_path(i))
    parts.append(f"<article class='story'><p class='kicker'>{e(st.get('kicker',''))}</p><h3>{e(st['title'])}</h3>{imgs}{body}<p class='proof'><b>Belege:</b> {e(st.get('proof',''))}</p></article>")
parts.append("</section>")

# Archivfunde
parts.append('<section class="kap" id="funde"><h2>Funde in Zeitungen und Archiven</h2>')
for it in FA["presse"]["items"]:
    im = it.get("img")
    src = ""
    if im:
        pth = os.path.join(PUB, im.lstrip("/")) if im.startswith("/") else os.path.join(PUB, "zeitung", f"{im}.webp")
        if os.path.exists(pth): src = druckbild(pth)
    parts.append(f"<article class='fund'><h3>{e(it.get('d',''))} · {e(it.get('paper',''))}</h3>{('<figure><img src=' + chr(39) + src + chr(39) + '></figure>') if src else ''}<blockquote>{e(it.get('t',''))}</blockquote><p>{e(it.get('m',''))}</p><p class='quelle'>Quelle: {e(it.get('paper',''))}, {e(it.get('d',''))}. {e(it.get('url',''))}</p></article>")
parts.append("</section>")

# Zeitleiste
rows = "".join(f"<tr><td class='j'>{e(t.get('d',''))}</td><td>{e(t.get('t',''))} {mark(t)}</td></tr>" for t in FA.get("timeline", []))
parts.append(f'<section class="kap" id="zeitleiste"><h2>Zeitleiste</h2><table class="zl">{rows}</table></section>')

# Forschung
neg = "".join(f"<li><b>{e(n.get('where',''))}</b>, {e(n.get('d',''))}: {e(n.get('q',''))}. {e(n.get('r',''))}</li>" for n in R["negatives"])
log = "".join(f"<li><b>{e(l.get('d',''))}, {e(l.get('how',''))}:</b> {e(l.get('t',''))}</li>" for l in R["log"])
nxt = "".join(f"<li><b>{e(n.get('st',''))}:</b> {e(n.get('t',''))}</li>" for n in R["next"])
qs = "".join(f"<li>{e(q.get('q',''))}</li>" for q in FA.get("questions", []))
parts.append(f"""<section class="kap" id="forschung"><h2>Stand der Forschung</h2>
<h3>Wo gesucht und nichts gefunden wurde</h3><ul class="klein">{neg}</ul>
<h3>Offene Aufgaben</h3><ul class="klein">{nxt}</ul>
<h3>Fragen an die Familie</h3><ul class="klein">{qs}</ul>
<h3>Forschungslog</h3><ul class="klein">{log}</ul></section>""")

# Quellen
groups = [("P", "Primärquellen"), ("S", "Abgeleitete Quellen"), ("E", "Erinnerungen"), ("I", "Fundhilfen"), ("K", "Kontext und Literatur")]
qparts = []
for c, h in groups:
    L2 = [s for s in FA["sources"] if (s.get("cls") or "K") == c]
    if L2:
        qparts.append(f"<h3>{h}</h3><ol class='qv'>" + "".join(f"<li><b>{e(s['id'])}</b> {e(zitat_lang(s))}</li>" for s in L2) + "</ol>")
parts.append(f'<section class="kap" id="quellen"><h2>Quellenverzeichnis</h2>{"".join(qparts)}</section>')

# Register
reg = "".join(f"<li><a href='#p-{pid}'>{e(p['name'])}</a>, S. <a class='pg' href='#p-{pid}'></a></li>" for pid, p in sorted(P.items(), key=lambda kv: kv[1]['name'].split(' ')[-1] + kv[1]['name']) if not (privat(p) and not p.get('facts')))
parts.append(f'<section class="kap" id="register"><h2>Personenregister</h2><ul class="reg">{reg}</ul></section>')

parts.append(f"""<section class="kap" id="daten"><h2>Zu den Daten</h2>
<p>Dieses Buch ist aus einer Datensammlung gesetzt. Sie liegt der archivfesten PDF-Ausgabe (PDF/A-3) als Anhang bei und kann mit jedem PDF-Programm herausgelöst werden. Die Formate sind offen und ohne Spezialprogramm lesbar:</p>
<ul><li><b>familienarchiv-junker.ged</b>: Stammbaum im Format GEDCOM 7.0, dazu eine Fassung in GEDCOM 5.5.1 für ältere Programme. Öffnen mit Gramps, Ancestris oder jedem Stammbaumprogramm.</li>
<li><b>archiv.json</b> mit <b>archiv.schema.json</b>: alle Daten vollständig, mit Beschreibung der Felder (JSON Schema).</li>
<li><b>aussagen.csv / aussagen.jsonl</b>: jede Aussage eine Zeile, mit Belegstufe, Sicherheit und Quellen. CSV öffnet jede Tabellenkalkulation (Trennzeichen Semikolon, Zeichensatz UTF-8).</li>
<li><b>personen.csv, familien.csv, quellen.csv, forschungslog.csv, negativbefunde.csv, offene-aufgaben.csv</b>.</li></ul>
<p>Die Fotos und Scans liegen im Bestand als Bilddateien mit ihrer Signatur im Dateinamen (Junker_0512.webp gehört zu DFA-JUN-F0512). Für die Langzeitsicherung empfiehlt sich: dieses Buch gedruckt, die PDF/A-Datei und die Bilder auf zwei Datenträgern an zwei Orten, alle paar Jahre auf neue Träger umkopiert.</p></section>""")

css = open(os.path.join(HERE, "buch.css"), encoding="utf-8").read().replace("{FONTS}", "file://" + os.path.join(HERE, "fonts"))
doc = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Familie Junker und Rückert</title>
<meta name="author" content="Till Heidrich"><meta name="description" content="Belegtes Familienarchiv, Stand {e(STAND)}"><meta name="keywords" content="Familiengeschichte, Junker, Rückert">
<style>{css}</style></head><body>{''.join(parts)}</body></html>"""
with open(os.path.join(B, "buch.html"), "w", encoding="utf-8") as fh:
    fh.write(doc)

# ---------- LIESMICH, RO-Crate, Prüfsummen ----------
liesmich = f"""# Familienarchiv Junker und Rückert, Archivpaket {STAND}

Dieses Verzeichnis ist die dauerhafte Fassung des Familienarchivs. Es braucht keine Website und kein Spezialprogramm.

- `buch/buch-druck-pdfx4.pdf`: druckfertiges Buch, 170 × 240 mm, mit 3 mm Beschnitt und Schnittmarken, PDF/X-4. So an eine Druckerei geben; Papier und Bindung mit der Druckerei abstimmen.
- `buch/buch-archiv-pdfa3.pdf`: dasselbe Buch als PDF/A-3b für die Langzeitarchivierung. Alle Daten aus `daten/` sind darin als Anhang eingebettet.
- `buch/buch.html`: Quelltext des Buchs.
- `daten/`: alle Daten in offenen Formaten (GEDCOM 7.0 und 5.5.1, JSON mit Schema, JSONL, CSV mit Semikolon, UTF-8).
- `ro-crate-metadata.json`: Beschreibung des Pakets nach RO-Crate 1.1 (JSON-LD), damit Programme und Archive den Inhalt erkennen.
- `SHA256SUMS.txt`: Prüfsummen. Mit `sha256sum -c SHA256SUMS.txt` lässt sich prüfen, ob eine Kopie unverändert ist.

Neu erzeugen: `python3 scripts/paket/build.py` im Repository des Archivs.

Datenschutz: Lebende Personen nur mit Jahreszahlen, keine Anschriften Lebender. Privat, nur für die Familie.
"""
with open(os.path.join(OUT, "LIESMICH.md"), "w", encoding="utf-8") as fh:
    fh.write(liesmich)

def build_pdfs():
    import weasyprint
    from weasyprint import Attachment
    html_obj = weasyprint.HTML(filename=os.path.join(B, "buch.html"), base_url=ROOT)
    druck_css = weasyprint.CSS(string="@page { bleed: 3mm; marks: crop cross; }")
    html_obj.write_pdf(os.path.join(B, "buch-druck-pdfx4.pdf"), stylesheets=[druck_css], pdf_variant="pdf/x-4")
    atts = [Attachment(filename=os.path.join(D, f), description=f) for f in sorted(os.listdir(D))]
    weasyprint.HTML(filename=os.path.join(B, "buch.html"), base_url=ROOT).write_pdf(os.path.join(B, "buch-archiv-pdfa3.pdf"), pdf_variant="pdf/a-3b", attachments=atts)

if "--ohne-pdf" not in sys.argv:
    build_pdfs()

files = []
for dp, _, fnames in os.walk(OUT):
    for f in fnames:
        files.append(os.path.relpath(os.path.join(dp, f), OUT))
crate = {"@context": "https://w3id.org/ro/crate/1.1/context", "@graph": [
    {"@id": "ro-crate-metadata.json", "@type": "CreativeWork", "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}, "about": {"@id": "./"}},
    {"@id": "./", "@type": "Dataset", "name": meta["titel"], "identifier": meta["signatur"], "datePublished": meta["erzeugt"],
     "description": "Belegtes Familienarchiv mit Stammbaum, Quellen, Belegstufen, Forschungslog und Buchfassung.",
     "author": {"@id": "#till"}, "license": meta["lizenz"], "hasPart": [{"@id": f} for f in sorted(files)]},
    {"@id": "#till", "@type": "Person", "name": "Till Heidrich", "affiliation": "Heidrich Digital"},
] + [{"@id": f, "@type": "File", "encodingFormat": {".json": "application/json", ".jsonl": "application/jsonl", ".csv": "text/csv", ".ged": "application/x-gedcom",
      ".pdf": "application/pdf", ".html": "text/html", ".md": "text/markdown"}.get(os.path.splitext(f)[1], "application/octet-stream")} for f in sorted(files)]}
with open(os.path.join(OUT, "ro-crate-metadata.json"), "w", encoding="utf-8") as fh:
    json.dump(crate, fh, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "SHA256SUMS.txt"), "w") as fh:
    for f in sorted(files + ["ro-crate-metadata.json"]):
        h = hashlib.sha256(open(os.path.join(OUT, f), "rb").read()).hexdigest()
        fh.write(f"{h}  {f}\n")
print(OUT)
