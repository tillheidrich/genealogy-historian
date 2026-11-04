"""Kontext für das Buch: Karten, Ahnentafeln, Zeitabschnitte, Familie und Welt, NS-Einordnung.

Gedacht für Leser, die die Zeit nicht mehr aus eigener Anschauung oder aus der Schule kennen.
Vermittlung nach Museumsart: drei Leseebenen (Überschrift, Kernsatz, Text), Objekt zuerst,
„Genau hinsehen“, Familie neben der Weltgeschichte, Fragen zum Weiterdenken, keine Überwältigung.
"""
import math, os, html, re

e = lambda t: html.escape(str(t or ""))
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "font-family:'Albert Sans'"
C = {"petrol": "#1e3c3e", "rost": "#9c3d1d", "land": "#ebe5d8", "see": "#dfe7e5", "grenze": "#b3aa98", "ink": "#191d1c", "mute": "#5b625f"}

# ---------------- Karten ----------------
def _laender():
    import shapefile
    r = shapefile.Reader(os.path.join(HERE, "karten", "naturalearth_lowres.shp"))
    out = []
    for sr in r.shapeRecords():
        pts, parts = sr.shape.points, list(sr.shape.parts) + [len(sr.shape.points)]
        out.append([pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)])
    return out

def _proj(lon0, lon1, lat0, lat1, W):
    k = math.cos(math.radians((lat0 + lat1) / 2))
    s = W / ((lon1 - lon0) * k)
    H = (lat1 - lat0) * s
    return (lambda lon, lat: ((lon - lon0) * k * s, (lat1 - lat) * s)), H, s

def km(a, b):
    R = 6371
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

# Regionen der Familie: Mittelpunkt, Beschriftung, Kategorie, Lage der Beschriftung (dx, dy in mm)
REGIONEN = []  # [Name, Unterzeile, [Orts-IDs], Kategorie, (dx, dy)]; in den Buchangaben unter "regionen" setzen
EXTRA = {}
FARBE = {"leben": C["rost"], "heute": "#7b2d22", "herkunft": C["petrol"], "krieg": "#5a2a1e", "atelier": "#6b5a7a", "arbeit": "#4a4238"}

def europakarte(PL, regionen=None, extra=None, bbox=None):
    pos = {p["id"]: tuple(p["ll"]) for p in PL["list"]}
    pos.update(EXTRA if extra is None else {k: tuple(v) for k, v in extra.items()})
    lon0, lon1, lat0, lat1 = bbox or (-5.4, 19.0, 46.0, 55.0)
    pj, H, s = _proj(lon0, lon1, lat0, lat1, 154)
    paths = []
    for poly in _laender():
        for ring in poly:
            if not any(lon0 - 8 < x < lon1 + 8 and lat0 - 6 < y < lat1 + 6 for x, y in ring):
                continue
            d = "M" + "L".join(f"{pj(x, y)[0]:.2f},{pj(x, y)[1]:.2f}" for x, y in ring) + "Z"
            paths.append(f"<path d='{d}'/>")
    g = []
    for name, sub, ids, cat, (dx, dy) in (regionen or REGIONEN):
        pts = [pos[i] for i in ids if i in pos]
        if not pts:
            continue
        la = sum(p[0] for p in pts) / len(pts); lo = sum(p[1] for p in pts) / len(pts)
        x, y = pj(lo, la)
        col = FARBE.get(cat, C["rost"])
        g.append(f"<circle cx='{x:.2f}' cy='{y:.2f}' r='1.25' fill='{col}' stroke='#fff' stroke-width='.35'/>")
        anchor = "end" if dx < 0 else "start"
        tx = x + (2.2 if dx > 0 else -2.2); ty = y + dy
        g.append(f"<text x='{tx:.2f}' y='{ty:.2f}' text-anchor='{anchor}' style=\"{FONT};font-weight:600\" font-size='2.7' fill='{C['ink']}'>{e(name)}</text>")
        g.append(f"<text x='{tx:.2f}' y='{ty + 3:.2f}' text-anchor='{anchor}' style=\"{FONT}\" font-size='2.2' fill='{C['mute']}'>{e(sub)}</text>")
    # Maßstab 200 km
    skm = 200 if (lat1 - lat0) > 4 else (50 if (lat1 - lat0) > 1.2 else 10)
    L = skm * s / 111.32
    sb = f"<g transform='translate({148 - L:.1f},{H - 6:.1f})'><rect width='{L:.2f}' height='.8' fill='{C['ink']}'/><text y='-1.6' style=\"{FONT}\" font-size='2.2' fill='{C['ink']}'>{skm} km</text></g>"
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 154 {H:.1f}' width='154mm' height='{H:.1f}mm'>"
            f"<defs><clipPath id='kc'><rect width='154' height='{H:.1f}'/></clipPath></defs>"
            f"<rect width='154' height='{H:.1f}' fill='{C['see']}'/><g clip-path='url(#kc)' fill='{C['land']}' stroke='{C['grenze']}' stroke-width='.25'>{''.join(paths)}</g>"
            f"{''.join(g)}{sb}</svg>"), H, pos

REVIER = []

ORIENT = []
def revierkarte(pos, punkte=None, orient=None, bbox=None, zentrum=None, zeche=""):
    lon0, lon1, lat0, lat1 = bbox
    pj, H, s = _proj(lon0, lon1, lat0, lat1, 154)
    g = []
    for n, la, lo in (ORIENT if orient is None else orient):
        x, y = pj(lo, la)
        g.append(f"<text x='{x:.2f}' y='{y:.2f}' text-anchor='middle' style=\"{FONT};font-weight:500;letter-spacing:.3\" font-size='3.4' fill='#b9ae99'>{e(n.upper())}</text>")
    zla, zlo = zentrum or ((lat0 + lat1) / 2, (lon0 + lon1) / 2)
    sx, sy = pj(zlo, zla)
    if zentrum: g.append(f"<circle cx='{sx:.2f}' cy='{sy:.2f}' r='{10 * s / 111.32:.2f}' fill='none' stroke='#cdbfa6' stroke-width='.35' stroke-dasharray='1.4 1'/>")
    for i, name, (dx, dy) in (punkte or REVIER):
        if i not in pos:
            continue
        la, lo = pos[i]
        x, y = pj(lo, la)
        ist_zeche = i == zeche
        g.append(f"<rect x='{x - 1.1:.2f}' y='{y - 1.1:.2f}' width='2.2' height='2.2' fill='{C['ink']}'/>" if ist_zeche else f"<circle cx='{x:.2f}' cy='{y:.2f}' r='1.1' fill='{C['rost']}' stroke='#fff' stroke-width='.3'/>")
        g.append(f"<text x='{x + dx:.2f}' y='{y + dy:.2f}' text-anchor='{'end' if dx < 0 else 'start'}' style=\"{FONT};font-weight:{600 if not ist_zeche else 500}\" font-size='2.8' fill='{C['ink']}'>{e(name)}</text>")
    L = 5 * s / 111.32
    sb = f"<g transform='translate(6,{H - 6:.1f})'><rect width='{L:.2f}' height='.8' fill='{C['ink']}'/><text y='-1.6' style=\"{FONT}\" font-size='2.4'>5 km</text></g>"
    nord = f"<g transform='translate(146,10)'><path d='M0,-5 L2,1 L0,0 L-2,1Z' fill='{C['ink']}'/><text y='5' text-anchor='middle' style=\"{FONT}\" font-size='2.4'>N</text></g>"
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 154 {H:.1f}' width='154mm' height='{H:.1f}mm'><rect width='154' height='{H:.1f}' fill='#f1ece1'/>"
            f"{''.join(g)}{sb}{nord}</svg>"), H

# ---------------- Ahnentafel ----------------
def _jahr(o):
    m = re.search(r"(\d{4})", str((o or {}).get("d", "")))
    return m.group(1) if m else ""

def _wrap(t, n=23):
    words, lines, cur = t.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    return lines[:2]

def ahnentafel(FA, root, H=196):
    P = FA["persons"]
    eltern = {}
    for c in FA["couples"]:
        for k in c.get("kids", []):
            eltern[k] = (c.get("a"), c.get("b"), bool(c.get("prob")))
    cols, cw, gap = 5, 27.6, 4.0
    boxes, lines = [], []
    def box(pid, gen, slot, unsicher=False):
        n = 2 ** gen; sh = H / n; cy = sh * (slot + .5)
        x = gen * (cw + gap); bh = min(14, sh - 1.6)
        p = P.get(pid) if pid else None
        if p:
            b, d = _jahr(p.get("born")), _jahr(p.get("died"))
            jahre = (f"{b}–{d}" if d else (f"* {b}" if b else "")) if (b or d) else "Jahre unbekannt"
            nm = _wrap(p["name"], 19 if gen < 3 else 20)
            fs = 2.5 if gen < 3 else 2.25
            t = "".join(f"<tspan x='{x + 2}' dy='{0 if i == 0 else fs * 1.15:.2f}'>{e(l)}</tspan>" for i, l in enumerate(nm))
            top = cy - (len(nm) * fs * 1.15 + 2.6) / 2 + fs
            fill = C["petrol"] if gen == 0 else "#fff"
            tc = "#f4efe5" if gen == 0 else C["ink"]
            boxes.append(f"<rect x='{x}' y='{cy - bh / 2:.2f}' width='{cw}' height='{bh:.2f}' rx='.6' fill='{fill}' stroke='{C['petrol'] if gen else 'none'}' stroke-width='.3'/>"
                         f"<text style=\"{FONT};font-weight:600\" font-size='{fs}' fill='{tc}' y='{top:.2f}'>{t}</text>"
                         f"<text x='{x + 2}' y='{top + len(nm) * fs * 1.15 + .6:.2f}' style=\"{FONT}\" font-size='{fs * .86:.2f}' fill='{'#c9d6d2' if gen == 0 else C['mute']}'>{e(jahre)}</text>")
        else:
            boxes.append(f"<rect x='{x}' y='{cy - bh / 2:.2f}' width='{cw}' height='{bh:.2f}' rx='.6' fill='none' stroke='{C['grenze']}' stroke-width='.3' stroke-dasharray='1 .8'/>"
                         f"<text x='{x + 2}' y='{cy + .8:.2f}' style=\"{FONT};font-style:italic\" font-size='2.2' fill='{C['mute']}'>noch nicht gefunden</text>")
        if gen < cols - 1:
            par = eltern.get(pid) if pid else None
            for j, ppid in enumerate((par[0], par[1]) if par else (None, None)):
                if not pid:
                    break
                cy2 = (H / 2 ** (gen + 1)) * (2 * slot + j + .5)
                x1 = x + cw; x2 = (gen + 1) * (cw + gap); xm = x1 + gap / 2
                dash = " stroke-dasharray='1.2 .9'" if par and par[2] else ""
                lines.append(f"<path d='M{x1},{cy:.2f} H{xm} V{cy2:.2f} H{x2}' fill='none' stroke='{C['petrol']}' stroke-width='.35'{dash}/>")
                box(ppid, gen + 1, 2 * slot + j)
    box(root, 0, 0)
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 154 {H}' width='154mm' height='{H}mm'>{''.join(lines)}{''.join(boxes)}</svg>"

# ---------------- Zeitabschnitte ----------------
EPOCHEN = [  # allgemeiner deutscher Rahmen; für jede Familie in den Buchangaben ("epochen") ergänzen
    ("vor 1871", "Viele Länder, Kirchenbücher, Landarbeit", "Deutschland besteht aus vielen Staaten. Die meisten Menschen leben auf dem Land; Taufen, Heiraten und Begräbnisse schreibt der Pfarrer ins Kirchenbuch."),
    ("1871–1914", "Kaiserreich", "1871 wird das Deutsche Kaiserreich gegründet. Preußen führt am 1. Oktober 1874 die Standesämter ein, das ganze Reich am 1. Januar 1876; seither gibt es für jede Geburt, Ehe und jeden Todesfall einen staatlichen Eintrag. Viele Familien ziehen dorthin, wo Fabriken und Zechen Arbeit bieten; Hunderttausende wandern nach Amerika aus."),
    ("1914–1918", "Erster Weltkrieg", "Im August 1914 beginnt der Krieg. Millionen Männer kommen an die Front, viele kehren nicht zurück. Nachrichten laufen über Feldpost, bei Gefangenen über das Internationale Komitee vom Roten Kreuz in Genf."),
    ("1918–1933", "Weimarer Republik", "Nach der Niederlage wird Deutschland Republik. Der Versailler Vertrag gibt Gebiete im Osten und Westen ab. 1923 vernichtet die Inflation die Ersparnisse, ab 1929 bringt die Weltwirtschaftskrise Massenarbeitslosigkeit."),
    ("1933–1945", "Nationalsozialismus und Zweiter Weltkrieg", "1933 kommt Hitler an die Macht, aus der Republik wird binnen Monaten eine Diktatur. Wer als Gegner gilt, wird verfolgt; Jüdinnen und Juden werden entrechtet, vertrieben und ab 1941 systematisch ermordet, rund sechs Millionen europäische Jüdinnen und Juden fallen dem Holocaust zum Opfer, dazu Sinti und Roma, Kranke und Behinderte und viele andere. Der Krieg, den Deutschland 1939 mit dem Überfall auf Polen beginnt, kostet mehr als 60 Millionen Menschen das Leben."),
    ("1945–1990", "Teilung und Wiederaufbau", "Die Gebiete östlich von Oder und Neiße werden polnisch und sowjetisch, Millionen Deutsche werden vertrieben; mit ihnen verschwinden Kirchenbücher und Ortsnamen. 1949 entstehen die Bundesrepublik und die DDR."),
    ("seit 1990", "Wiedervereinigung und Gegenwart", "1990 wird Deutschland wiedervereinigt. Archive öffnen und digitalisieren ihre Bestände, vieles ist heute online."),
]
LESETIPP = "Zum Nachlesen: LeMO – Lebendiges Museum Online, Deutsches Historisches Museum und Haus der Geschichte, www.dhm.de/lemo."

WELT = [("1871", "Gründung des Deutschen Kaiserreichs"), ("1874", "Standesämter in Preußen (Reich 1876)"), ("1914", "Beginn des Ersten Weltkriegs"), ("1918", "Kriegsende, Deutschland wird Republik"), ("1923", "Inflation"), ("1929", "Weltwirtschaftskrise"), ("1933", "Hitler wird Reichskanzler"), ("1939", "Beginn des Zweiten Weltkriegs"), ("1945", "Kriegsende"), ("1949", "Gründung von Bundesrepublik und DDR"), ("1969", "Mondlandung"), ("1989", "Fall der Mauer"), ("1990", "Wiedervereinigung")]

def familie_und_welt(FA, P, welt_liste=None):
    fam = {}
    for t in FA.get("timeline", []):
        m = re.search(r"(\d{4})", str(t.get("d", "")))
        if m:
            fam.setdefault(m.group(1), []).append(t.get("t", ""))
    welt = {}
    for j, t in (welt_liste or WELT):
        welt.setdefault(j, []).append(t)
    jahre = sorted(set(fam) | set(welt), key=int)
    rows = "".join(f"<tr><td class='j'>{j}</td><td>{'<br>'.join(e(x) for x in fam.get(j, []))}</td><td class='w'>{'<br>'.join(e(x) for x in welt.get(j, []))}</td></tr>" for j in jahre)
    return f"<table class='fw'><tr><th></th><th>In der Familie</th><th>In der Welt</th></tr>{rows}</table>"

# ---------------- NS-Einordnung ----------------
SP1 = ("So hat der SPIEGEL die Daten aus der Nazi-Kartei aufbereitet", "Susmita Arp u. a., DER SPIEGEL, 07.05.2026", "https://www.spiegel.de/geschichte/nsdap-mitgliederkartei-die-wichtigsten-fakten-ueber-die-nazi-datenbank-a-6c7882bb-68a6-448f-86e6-52fb78e6e7fe")
SP2 = ("„Niemand ist durch unmittelbaren Zwang in die NSDAP eingetreten“", "Katja Iken, Interview mit Johannes Spohr, DER SPIEGEL, 28.03.2026", "https://www.spiegel.de/geschichte/nationalsozialismus-interview-mit-johannes-spohr-historiker-niemand-ist-durch-zwang-in-die-nsdap-eingetreten-a-3fbc5100-e5cf-438c-9cca-f9aa8bd2feb8")
SP3 = ("Hier erfahren Sie, was Ihre Großeltern in der Nazizeit gemacht haben", "Frederik Seeler, DER SPIEGEL, 17.03.2026", "https://www.spiegel.de/geschichte/waren-opa-und-oma-nazis-nsdap-mitgliedskarteien-kann-man-jetzt-online-durchsuchen-a-4eccb8da-2ac9-433c-a30a-a366f995dc2c")
def _fn(sp):
    return f"<span class='fn'>{e(sp[0])}. {e(sp[1])}, {e(sp[2])} (abgerufen 04.11.2026).</span>"

def ns_einordnung():
    return f"""<section class='kap ns-kontext'><h2>Was die NSDAP war</h2>
<p class='lead'>Die Nationalsozialistische Deutsche Arbeiterpartei regierte Deutschland von 1933 bis 1945 als einzige erlaubte Partei. Sie verantwortete Diktatur, Krieg und den Mord an den europäischen Jüdinnen und Juden. Wer in diesem Buch eine Karteikarte findet, soll verstehen können, was sie bedeutet und was nicht.</p>
<h3>Wie man Mitglied wurde</h3>
<p>Ab dem 1. Mai 1933 nahm die Partei zunächst keine neuen Mitglieder auf. Ab 1937 öffnete sie sich wieder, ab 1939 für alle; im Krieg warb sie vor allem in der Hitlerjugend und im Bund Deutscher Mädel um Nachwuchs. Bei Kriegsende waren knapp neun Millionen Menschen Mitglied.{_fn(SP1)} Automatisch wurde niemand aufgenommen: Für jede Aufnahme brauchte es einen eigenhändig unterschriebenen Antrag.{_fn(SP1)} Es gab sozialen Druck und Berufe, in denen die Mitgliedschaft Vorteile brachte, aber niemand trat ohne eigenes Zutun oder durch unmittelbaren Zwang ein.{_fn(SP2)}</p>
<h3>Was eine Karte sagt und was nicht</h3>
<p>Eine Karteikarte belegt eine Mitgliedschaft, nicht eine Gesinnung und keine Tat. Historiker nennen den Fund den Anfang einer Nachforschung, nicht ihr Ergebnis.{_fn(SP2)} Viel sagt das Eintrittsdatum: Wer schon vor 1933 eintrat, war eher überzeugter Nationalsozialist.{_fn(SP3)} Umgekehrt entlastet es niemanden, nicht in der Kartei zu stehen: Rund ein Fünftel der Karten ist verloren.{_fn(SP2)}</p>
<h3>Genau hinsehen</h3>
<ul class='einord'><li><b>Zwei Karten je Person.</b> Die Partei führte eine alphabetische Zentralkartei und eine nach Gauen und Ortsgruppen geordnete Gaukartei; darum gibt es zu manchen Menschen zwei Karten.{_fn(SP1)}</li>
<li><b>Buchstabenstempel.</b> Ein A, C oder K auf der Karte stammt meist von den Amerikanern nach 1945: A heißt, ein Aufnahmeantrag liegt vor; C, ein Bogen der Parteistatistik von 1939; K, es gibt auch eine Karte in der Zentralkartei.{_fn(SP1)}</li>
<li><b>Wie die Karten überliefert sind.</b> Die Kartei lag bis 1945 in München. Der Leiter einer Papiermühle sollte sie vernichten, versteckte sie und übergab sie der US-Armee; heute liegt sie im Bundesarchiv (Bestand R 9361).{_fn(SP1)}</li></ul>
<p class='frage'><b>Zum Weiterdenken.</b> Was wusste man 1939 in einem Dorf über das Regime? Was hätte ein Nein gekostet, und was ein Ja gebracht? Die Karten beantworten diese Fragen nicht; Briefe, Erzählungen und Entnazifizierungsakten können es manchmal.</p></section>"""

# ---------------- Lesehilfen ----------------
REGISTER_HILFE = """<section class='kap hilfe'><h2>So liest man einen Registereintrag</h2>
<p class='lead'>Seit 1874 hält in Preußen ein Standesbeamter jede Geburt, Ehe und jeden Todesfall fest. Die Einträge folgen einem gedruckten Formular, und wer das Formular kennt, findet sich auch in der Handschrift zurecht.</p>
<ul class='einord'><li><b>Oben links</b> steht die Nummer des Eintrags im Jahrgang, zum Beispiel „Nr. 12“. Mit Ort, Jahr und Nummer lässt sich jeder Eintrag wiederfinden.</li>
<li><b>Der Kopf</b> nennt Ort und Datum der Anzeige, nicht unbedingt des Ereignisses. Wer anzeigt, steht darunter: bei Geburten meist der Vater oder die Hebamme, bei Todesfällen ein Angehöriger oder Nachbar.</li>
<li><b>Die Mitte</b> enthält, was geschehen ist, mit Namen, Beruf, Wohnort und Religion der Beteiligten. Bei Heiraten kommen Eltern und zwei Trauzeugen hinzu.</li>
<li><b>Am Rand</b> stehen spätere Nachträge: eine Heirat, ein Tod, eine Namensänderung, oft Jahrzehnte später eingetragen. Sie sind für Familienforscher oft der wertvollste Teil.</li>
<li><b>Die Schrift</b> ist meist deutsche Kurrentschrift oder Sütterlin. Jede Seite in diesem Buch zeigt daher neben dem Scan eine Abschrift in heutiger Schrift.</li></ul></section>"""

FOTO_HILFE = """<p class='hinweis'><b>Genau hinsehen.</b> Alte Fotos erzählen mehr als ihre Gesichter: der Karton und der Stempel des Ateliers verraten Ort und ungefähre Zeit, Uniformen und Kleidung das Jahrzehnt, und die Rückseiten tragen oft Namen, Grüße und Daten. Wo eine Rückseite beschriftet ist, steht ihr Wortlaut in der Bildunterschrift.</p>"""
