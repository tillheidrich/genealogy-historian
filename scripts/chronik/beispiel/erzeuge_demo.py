"""Beispiel und Schema: die erfundene Familie Hollenbeck aus Kehdingen (wie auf dasfamilienarchiv.de/demo).
Alle Namen, Daten und Quellen sind erfunden. Aufruf: python3 erzeuge_demo.py && python3 ../build.py --daten demo-hollenbeck.js --ausgabe paket
Die Struktur von FA ist das Datenschema für eigene Familien: Personen, Paare, Quellen, Belegstufen, Geschichten, Fakten,
Urkunden, Presse, Forschungslog, Orte und unter "buch" alle Angaben für Titel, Karten, Ahnentafeln und Kolophon."""
import json, os, subprocess, sys
HIER = os.path.dirname(os.path.abspath(__file__))
lv = {
 "U": {
  "label": "Urkunde",
  "long": "Eintrag im Standesamtsregister, Scan eingesehen"
 },
 "R": {
  "label": "Randvermerk",
  "long": "Spätere amtliche Eintragung am Rand eines Registereintrags"
 },
 "A": {
  "label": "Archivkarte",
  "long": "Karteikarte oder Akte eines staatlichen Archivs, Scan eingesehen. Zugeordnet über Name, Geburtsdatum und Wohnort."
 },
 "Z": {
  "label": "Zeitung, Druck",
  "long": "Zeitungsmeldung, Amtsblatt oder Adressbuch, Originalscan eingesehen. Ob die Meldung unsere Person meint, steht beim Fund dabei."
 },
 "F": {
  "label": "Familienunterlage",
  "long": "Familienchronik 2012 oder maschinenschriftliche Familiennotiz; nicht mit Registern abgeglichen"
 },
 "B": {
  "label": "Beschriftung",
  "long": "Handschrift, Stempel oder Aufdruck auf einem Foto oder Zettel"
 },
 "E": {
  "label": "Erinnerung",
  "long": "Erzählung oder Zuordnung durch die Familie (Tonaufnahme, Film, Angabe von Till)"
 },
 "L": {
  "label": "Literatur, Index",
  "long": "Fachliteratur, Nachschlagewerk, Forenbeitrag, Online-Index oder Datenbank (z. B. FamilySearch-Index, Verlustlisten-Index). Das Original ist nicht eingesehen; dient als Findhilfe und zur Absicherung."
 },
 "H": {
  "label": "Vermutung",
  "long": "Schluss der Bearbeitung aus mehreren Indizien, nicht belegt"
 },
 "O": {
  "label": "offen",
  "long": "Quellen widersprechen sich oder fehlen"
 }
}

Q = lambda i, cls, kind, t, d, w: {"id": i, "cls": cls, "kind": kind, "title": t, "detail": d, "where": w}
sources = [
    Q("ASSEL-G", "P", "U", "Geburtsregister Standesamt Assel", "Jahrgänge 1877, 1905, 1908 (erfunden)", "Kreisarchiv Stade, Zweitschriften"),
    Q("ASSEL-H", "P", "U", "Heiratsregister Standesamt Assel 1904", "Nr. 9/1904 (erfunden)", "Kreisarchiv Stade"),
    Q("ASSEL-S", "P", "U", "Sterberegister Standesamt Assel 1951", "Nr. 2/1951 (erfunden)", "Standesamt Drochtersen"),
    Q("KB-DRO", "P", "U", "Ev.-luth. Kirchenbuch Drochtersen, Taufen 1881", "S. 14, Nr. 6 (erfunden)", "Kirchenkreisarchiv Stade"),
    Q("HH-PASS", "P", "A", "Hamburger Passagierlisten 1903", "Schiff „Pennsylvania“, April 1903, Zeile 211 (erfunden)", "Staatsarchiv Hamburg, Bestand 373-7 I, VIII"),
    Q("KREISBL", "S", "Z", "Kehdinger Kreisblatt, 12.05.1906", "Anzeige Hofverkauf (erfunden)", "Zeitungsarchiv Stade"),
    Q("BIBEL", "S", "F", "Familienbibel Hollenbeck", "Eintragungen um 1910, Handschrift", "Familienbesitz"),
    Q("FOTO31", "S", "B", "Foto „Grete u. Hinni“, 1931", "Beschriftete Rückseite im Album", "Familienbesitz"),
    Q("GESELLE", "S", "F", "Gesellenbrief Karl Behrens, 1952", "noch nicht abgeschrieben", "Familienbesitz"),
    Q("ILSE", "E", "E", "Gespräche mit Ilse Behrens", "Drei Tonaufnahmen 2025, mit Zustimmung", "Familienbesitz"),
    Q("VOLKSB", "I", "O", "Gräbersuche online, Volksbund", "Suche nach Johann Hollenbeck, ohne Treffer", "volksbund.de"),
    Q("BARCH", "I", "O", "Anfrage Bundesarchiv, Abteilung PA", "gestellt 14.03.2025, Antwort steht aus", "Bundesarchiv"),
]
def f(t, l, src, sich=None):
    d = {"t": t, "lvl": l, "src": src}
    if sich:
        d["sich"] = sich
    return d
persons = {
    "claus_mohr": {"name": "Claus Mohr", "gen": -3, "fam": "Mohr", "born": {"d": "um 1850", "lvl": "H", "src": []}, "facts": [f("Vater von Anna laut Taufbuch, Häusling in Drochtersen.", "U", ["KB-DRO"])]},
    "metta_tiedemann": {"name": "Metta Mohr geb. Tiedemann", "gen": -3, "fam": "Mohr", "facts": [f("Mutter von Anna laut Taufbuch.", "U", ["KB-DRO"])]},
    "heinrich": {"name": "Heinrich Hollenbeck", "gen": -2, "fam": "Hollenbeck", "born": {"d": "03.03.1877", "p": "Assel", "lvl": "U", "src": ["ASSEL-G 1877"]}, "died": {"d": "09.01.1951", "p": "Assel", "lvl": "U", "src": ["ASSEL-S"]},
                 "facts": [f("Kleinbauer und Torfstecher in Assel.", "U", ["ASSEL-S"]), f("Wanderte im April 1903 über Hamburg nach New York aus.", "A", ["HH-PASS"]),
                           f("Kam 1906 zurück und kaufte einen Hof am Deich.", "Z", ["KREISBL"]), f("Soll in Amerika „reich geworden“ sein.", "E", ["ILSE"])]},
    "anna": {"name": "Anna Hollenbeck geb. Mohr", "gen": -2, "fam": "Hollenbeck", "born": {"d": "02.02.1881", "p": "Drochtersen", "lvl": "U", "src": ["KB-DRO"]}, "died": {"d": "1960", "p": "Assel", "lvl": "E", "src": ["ILSE"]},
             "alt": "Laut Familienbibel 1880 geboren; das Taufbuch ist näher am Ereignis und gilt.", "facts": [f("Heirat mit Heinrich am 14.05.1904 in Assel.", "U", ["ASSEL-H"])]},
    "johann": {"name": "Johann Hollenbeck", "gen": -1, "fam": "Hollenbeck", "born": {"d": "21.08.1905", "p": "Assel", "lvl": "U", "src": ["ASSEL-G 1905"]},
               "facts": [f("Soll im Sommer 1944 an der Ostfront gefallen sein.", "E", ["ILSE"]), f("Ein Grab oder eine Todesmeldung ist nicht gefunden; er gilt als vermisst.", "O", ["VOLKSB", "BARCH"])]},
    "grete": {"name": "Grete Behrens geb. Hollenbeck", "gen": -1, "fam": "Hollenbeck", "born": {"d": "11.06.1908", "p": "Assel", "lvl": "U", "src": ["ASSEL-G 1908"]}, "died": {"d": "1990", "p": "Stade", "lvl": "E", "src": ["ILSE"]},
              "facts": [f("Auf einem Foto von 1931 mit „Grete u. Hinni“ beschriftet.", "B", ["FOTO31"])]},
    "hinrich": {"name": "Hinrich Behrens", "gen": -1, "fam": "Behrens", "facts": [f("„Hinni“ auf dem Foto von 1931 ist vermutlich er.", "H", ["FOTO31"], "möglich")]},
    "karl": {"name": "Karl Behrens", "gen": 0, "fam": "Behrens", "born": {"d": "1934", "p": "Stade", "lvl": "E", "src": ["ILSE"]}, "died": {"d": "2011", "p": "Hamburg", "lvl": "E", "src": ["ILSE"]},
             "facts": [f("Lernte Schiffbau auf einer Werft in Hamburg.", "E", ["ILSE"]), f("Gesellenbrief von 1952 im Familienbesitz.", "F", ["GESELLE"])]},
    "ilse": {"name": "Ilse Behrens", "gen": 0, "fam": "Behrens", "living": True, "born": {"d": "1936", "lvl": "E", "src": ["ILSE"]},
             "facts": [f("Erzählt die Familiengeschichte; drei Gespräche aufgenommen.", "E", ["ILSE"])]},
}
couples = [{"a": "claus_mohr", "b": "metta_tiedemann", "kids": ["anna"]},
           {"a": "heinrich", "b": "anna", "m": {"d": "14.05.1904, Assel", "lvl": "U", "src": ["ASSEL-H"]}, "kids": ["johann", "grete"]},
           {"a": "hinrich", "b": "grete", "prob": "Ehe noch ohne Urkunde", "kids": ["karl", "ilse"]}]
timeline = [{"d": "1877", "t": "Heinrich Hollenbeck wird in Assel geboren.", "lvl": "U"}, {"d": "1881", "t": "Anna Mohr wird in Drochtersen getauft.", "lvl": "U"},
            {"d": "1903", "t": "Heinrich fährt von Hamburg nach New York.", "lvl": "A"}, {"d": "1904", "t": "Heinrich und Anna heiraten in Assel.", "lvl": "U"},
            {"d": "1906", "t": "Heinrich kauft einen Hof am Deich.", "lvl": "Z"}, {"d": "1931", "t": "Foto „Grete u. Hinni“.", "lvl": "B"},
            {"d": "1944", "t": "Johann gilt seitdem als vermisst.", "lvl": "E"}, {"d": "1951", "t": "Heinrich stirbt in Assel.", "lvl": "U"},
            {"d": "1952", "t": "Karl wird Schiffbaugeselle.", "lvl": "F"}, {"d": "2025", "t": "Ilse erzählt in drei Gesprächen die Familiengeschichte.", "lvl": "E"}]
stories = [
    {"id": "amerika", "kicker": "1903 · 1906", "title": "Opa Heinrich war in Amerika",
     "body": ["„Der Opa war doch drüben in Amerika, und mit dem Geld hat er dann den Hof gekauft.“ So erzählt es Ilse. Kein Jahr, kein Ort, aber zwei Behauptungen, die sich prüfen lassen: die Auswanderung und der Hofkauf.",
              "Die Hamburger Passagierlisten nennen im April 1903 einen Heinrich Hollenbeck, 26 Jahre, Arbeiter, aus Assel, Ziel New York. Name, Alter und Ort passen zum Geburtseintrag von 1877, und im Kreis gab es keinen zweiten Heinrich Hollenbeck dieses Jahrgangs.",
              "1906 erscheint im Kehdinger Kreisblatt eine Anzeige: Der Hof am Deich wird „an H. Hollenbeck, zurück aus Amerika“ verkauft. Einen Kaufpreis nennt sie nicht.",
              "Ob er reich wurde, sagt keine Quelle. Drei Jahre Arbeit in Amerika reichten damals oft für einen kleinen Hof, mehr nicht. Der Kern der Erzählung stimmt, die Übertreibung kam später dazu. Das ist der Normalfall."],
     "proof": "Hamburger Passagierlisten 1903 (A), Kehdinger Kreisblatt 1906 (Z), Erzählung Ilse (E). Amerikanische Einbürgerungs- und Zensusakten noch nicht durchgesehen.", "images": []},
    {"id": "anna", "kicker": "1880 oder 1881", "title": "Wie alt war Anna?",
     "body": ["In der Familienbibel steht „Anna geb. 1880“. Das Taufbuch von Drochtersen nennt den 2. Februar 1881, eingetragen wenige Tage nach der Geburt vom Pfarrer, und das Heiratsregister von 1904 gibt ihr Alter mit 23 Jahren an. Das passt zu 1881.",
              "Gültig ist 1881, weil diese Quelle dem Ereignis am nächsten ist. Der Eintrag in der Bibel bleibt trotzdem im Archiv stehen, mit dem Hinweis, dass er abweicht. Wer später die Bibel findet, soll nicht denken, man habe sie übersehen."],
     "proof": "Taufbuch Drochtersen 1881 (U), Heiratsregister Assel 1904 (U), Familienbibel um 1910 (F).", "images": []},
    {"id": "johann", "kicker": "1944", "title": "Johann, vermisst",
     "body": ["Ilse erinnert sich, dass ihr Onkel Johann im Sommer 1944 an der Ostfront gefallen sein soll. Eine Todesmeldung gibt es in der Familie nicht, ein Grab ist in der Gräbersuche des Volksbunds nicht verzeichnet.",
              "Johann gilt deshalb als vermisst, nicht als gefallen. Beim Bundesarchiv liegt eine Anfrage nach seinen Wehrmachtsunterlagen; der Suchdienst des Roten Kreuzes ist die nächste Adresse. Manchmal tauchen in solchen Akten Feldpostnummern, Einheiten und ein letzter Meldeort auf."],
     "proof": "Erzählung Ilse (E); Volksbund ohne Treffer (O); Anfrage Bundesarchiv offen (O).", "images": []},
]
fakten = [
    {"k": "Was wir sicher wissen", "t": "Heinrich Hollenbeck war von 1903 bis 1906 in Amerika und kaufte danach einen Hof am Deich.", "lvl": "A", "src": ["HH-PASS", "KREISBL"], "how": "Passagierliste und Zeitungsanzeige unabhängig voneinander gefunden; Alter und Herkunft stimmen mit dem Geburtsregister."},
    {"k": "Was wir sicher wissen", "t": "Anna Mohr ist 1881 geboren, nicht 1880.", "lvl": "U", "src": ["KB-DRO", "ASSEL-H"], "how": "Taufbuch und Heiratsalter stimmen überein; die Bibel wurde fast dreißig Jahre später geschrieben."},
    {"k": "Was offen ist", "t": "Wo und wann Johann Hollenbeck 1944 starb, ist unbekannt.", "lvl": "O", "src": ["VOLKSB", "BARCH"], "how": "Gräbersuche ohne Treffer, Anfrage beim Bundesarchiv gestellt."},
    {"k": "Was offen ist", "t": "Ob „Hinni“ auf dem Foto von 1931 Hinrich Behrens ist, ist eine Vermutung.", "lvl": "H", "src": ["FOTO31"], "how": "Vorname, Jahr und Ort passen; eine Heiratsurkunde fehlt noch."},
]
docs = [{"id": "U-DEMO-1", "title": "Taufeintrag Anna Mohr, 1881 (nachgestellt)", "archive": "Ev.-luth. Kirchenbuch Drochtersen, Taufen 1881, Nr. 6",
         "lesung": "Beispiel: Der Eintrag ist für diese Demo erfunden und hier in heutiger Schrift gesetzt; in einer echten Chronik steht darüber der Scan des Originals.",
         "transcript": ["Nr. 6. Anna Margaretha, geboren den 2. Februar 1881, getauft den 13. Februar 1881.", "Vater: Claus Mohr, Häusling zu Drochtersen. Mutter: Metta geb. Tiedemann.", "Pathen: Margaretha Tiedemann, Anna Hollmann."],
         "assess": ["Kirchenbücher sind vor 1874 die wichtigste Quelle für Geburten. Der Eintrag nennt die Eltern und macht die nächste Generation auffindbar.", "Die Taufe folgte elf Tage nach der Geburt, damals üblich."]}]
presse = {"items": [{"d": "12.05.1906", "paper": "Kehdinger Kreisblatt (erfunden)", "h": "Hof am Deich verkauft",
                     "t": "Die Hofstelle am Deich, bisher Wwe. Stelling, ist an H. Hollenbeck, zurück aus Amerika, übergegangen.", "m": "Die Anzeige bestätigt Rückkehr und Hofkauf. Den Preis nennt sie nicht, die Erzählung vom Reichtum bleibt unbelegt."}],
          "glossar": {"haeusling": {"t": "Häusling", "d": "Jemand, der in einem fremden Haus zur Miete wohnte und sich als Tagelöhner verdingte; im Gegensatz zum Hofbesitzer."},
                      "torf": {"t": "Torfstecher", "d": "Arbeiter, der im Moor Torf als Brennstoff aus dem Boden stach. In Kehdingen bis ins 20. Jahrhundert ein Nebenerwerb."},
                      "kreisblatt": {"t": "Kreisblatt", "d": "Amtliche Zeitung eines Landkreises mit Bekanntmachungen, Anzeigen und Nachrichten aus der Gegend."},
                      "passagierliste": {"t": "Passagierliste", "d": "Liste der Reisenden eines Auswandererschiffs mit Name, Alter, Beruf, Herkunft und Ziel; in Hamburg von 1850 bis 1934 erhalten."},
                      "vermisst": {"t": "vermisst", "d": "Ein Soldat, dessen Tod nicht gemeldet und dessen Grab nicht bekannt ist. Viele Familien warteten nach 1945 jahrelang auf Nachricht."}}}
research = {"log": [{"d": "12.03.2025", "how": "Passagierlisten Hamburg", "t": "Hollenbeck, 1900–1910: ein Treffer, April 1903, zugeordnet."},
                    {"d": "12.03.2025", "how": "Zeitungsportal", "t": "Hollenbeck, Assel, 1903–1910: Anzeige Hofkauf 1906."},
                    {"d": "18.03.2025", "how": "Kirchenbuch Drochtersen", "t": "Taufe Anna Mohr, 1880–1881: gefunden, 2. Februar 1881."}],
            "negatives": [{"d": "14.03.2025", "where": "Gräbersuche Volksbund", "q": "Johann Hollenbeck, geb. 1905", "r": "Kein Treffer."},
                          {"d": "14.03.2025", "where": "Ellis-Island-Datenbank", "q": "Ankunft 1903", "r": "Kein Treffer, Schreibweise prüfen."}],
            "next": [{"st": "offen", "t": "Amerikanische Zensus- und Einbürgerungsakten 1903–1906 durchsehen."}, {"st": "offen", "t": "Heiratsurkunde Grete und Hinrich Behrens bestellen."},
                     {"st": "offen", "t": "Suchdienst des DRK zu Johann Hollenbeck anfragen."}]}
questions = [{"q": "Hat Opa Heinrich erzählt, wo in Amerika er gearbeitet hat?"}, {"q": "Wer ist „Hinni“ auf dem Foto von 1931?"}, {"q": "Gab es von Johann noch Feldpost oder eine Vermisstenmeldung?"}]
orte = [{"id": "assel", "ll": [53.680, 9.427]}, {"id": "drochtersen", "ll": [53.712, 9.384]}, {"id": "stade", "ll": [53.600, 9.476]}, {"id": "hamburg", "ll": [53.550, 9.993]}, {"id": "cuxhaven", "ll": [53.861, 8.694]}]
epochen = [
    ("1866–1914", "Preußen, Kaiserreich und Auswanderung", "1866 wird das Königreich Hannover und mit ihm Kehdingen preußisch. Wer an der Unterelbe keinen Hof erbt, arbeitet als Knecht, Tagelöhner oder Torfstecher. Über Hamburg wandern Hunderttausende nach Amerika aus; manche kehren nach ein paar Jahren mit Ersparnissen zurück. Seit 1874 gibt es Standesämter, davor nur Kirchenbücher."),
    ("1914–1933", "Krieg, Republik, Inflation", "Der Erste Weltkrieg holt die jungen Männer aus den Dörfern an die Front. Nach 1918 wird Deutschland Republik; 1923 vernichtet die Inflation die Ersparnisse, ab 1929 trifft die Weltwirtschaftskrise auch die Landwirtschaft."),
    ("1933–1945", "Nationalsozialismus und Krieg", "1933 kommt Hitler an die Macht. Der Zweite Weltkrieg, den Deutschland 1939 beginnt, kostet mehr als 60 Millionen Menschen das Leben; rund sechs Millionen europäische Jüdinnen und Juden werden ermordet. Von vielen Soldaten an der Ostfront erfahren die Familien nie, wo sie gestorben sind; sie gelten als vermisst."),
    ("1945–1990", "Nachkriegszeit und Werften", "Flüchtlinge aus dem Osten kommen auch nach Kehdingen. Die Hamburger Werften suchen Arbeiter, viele junge Männer aus dem Umland lernen dort. Im Februar 1962 überflutet eine Sturmflut weite Teile Hamburgs und der Elbmarschen; danach werden die Deiche erhöht."),
    ("seit 1990", "Gegenwart", "Archive digitalisieren ihre Bestände, Passagierlisten und Kirchenbücher sind online. 2025 erzählt Ilse in drei Gesprächen die Familiengeschichte, und aus ihren Erinnerungen und den Funden entsteht diese Chronik."),
]
welt = [("1866", "Hannover wird preußisch"), ("1874", "Standesämter in Preußen"), ("1892", "Ellis Island eröffnet"), ("1914", "Beginn des Ersten Weltkriegs"), ("1923", "Inflation"),
        ("1933", "Hitler wird Reichskanzler"), ("1939", "Beginn des Zweiten Weltkriegs"), ("1945", "Kriegsende"), ("1949", "Gründung der Bundesrepublik"), ("1962", "Sturmflut an der Elbe"), ("1990", "Wiedervereinigung")]
beispiel = []  # eigene Fotos: [{"datei": "/pfad/foto.webp", "sig": "Signatur", "cap": "Bildunterschrift"}]
buch = {
    "titel_html": "Familie Hollenbeck<br>aus Kehdingen", "titel": "Familie Hollenbeck aus Kehdingen", "untertitel_html": "Kleinbauern, Auswanderer und Werftarbeiter an der Unterelbe.<br>Eine Demo-Chronik mit einer erfundenen Familie",
    "signatur": "DEMO-HOL-01", "kurz": "DEMO-HOL", "bildprefix": "Hollenbeck_", "bilderdir": "/nicht/vorhanden", "cover": "-", "hg": "Demo von dasfamilienarchiv.de", "autor": "Heidrich Digital", "ki_modell": "Claude Opus 5.5", "ki_zeitraum": "im November 2026",
    "impressum_html": "<p><b>Diese Familie ist erfunden.</b> Namen, Daten, Orte, Urkunden und Zeitungsmeldungen dieser Demo sind Beispiele und gehören keiner echten Person. Die Arbeitsweise ist echt: genauso entstehen die Chroniken auf dasfamilienarchiv.de.</p>",
    "vorwort_html": "<p class='lead'>So sieht eine fertige Familienchronik aus: mit Karten, Stammbaum, Zeitabschnitten, Geschichten, Urkunden, Belegen und einem Anhang für alle, die es genau wissen wollen. Diese Demo zeigt es an einer erfundenen Familie aus Kehdingen an der Unterelbe.</p>",
    "karte_lead_html": "<p class='lead'>Die Hollenbecks lebten fast zweihundert Jahre zwischen Elbe und Moor. Weiter weg kam nur Heinrich: über Hamburg nach New York und zurück.</p>",
    "karte_hinweis": "Grenzen von heute. New York liegt rund 6 000 km westlich von Hamburg.",
    "entfernungen": [["assel", "hamburg", "Assel–Hamburg"], ["assel", "stade", "Assel–Stade"]],
    "regionen": [["Assel und Drochtersen", "Hof am Deich, Kirche, Standesamt", ["assel", "drochtersen"], "leben", [-1, -3]], ["Stade", "Kreisarchiv, Grete und Karl", ["stade"], "leben", [1, 3]],
                 ["Hamburg", "Auswandererhafen, Werften", ["hamburg"], "krieg", [1, -2]], ["Cuxhaven", "Abfahrt der Schiffe", ["cuxhaven"], "atelier", [-1, 3]]],
    "orte_extra": {}, "karte_bbox": [8.2, 10.6, 53.3, 54.05], "revier": False, "wurzeln": [["ilse", "Ilse"]],
    "gen_namen": {"-3": "Urgroßeltern von Ilse", "-2": "Großeltern von Ilse", "-1": "Eltern von Ilse", "0": "Ilse und ihr Bruder"},
    "familie_html": "<p>Für eine echte Chronik liefert die Familie das Wichtigste: Fotoalben, Papiere, Erinnerungen und die Entscheidung, was hineinkommt. In dieser Demo steht dafür Ilse Behrens, eine erfundene Erzählerin; ihre drei Gespräche sind ebenfalls erfunden.</p>",
    "ki_html": "<p>In einer echten Chronik liest die KI Urkunden und Zeitungen, sucht in Online-Archiven, schreibt ab, übersetzt, entwirft Texte und setzt das Buch. Ein Mensch prüft jeden Treffer am Scan, vergibt die Belegstufen und entscheidet Widersprüche.</p>",
    "rueck_html": "<p>Eine Demo-Chronik von dasfamilienarchiv.de: eine erfundene Familie, echte Arbeitsweise. Karten, Stammbaum, Geschichten, Urkunden mit Abschrift und Belege, druckfertig für jede Druckerei und als archivfeste PDF mit allen Daten.</p>",
    "epochen": epochen, "epochen_titel": "Hundertfünfzig Jahre in fünf Abschnitten", "welt": welt,
    "lesetipp": "Zum Nachlesen: LeMO – Lebendiges Museum Online, www.dhm.de/lemo.",
    "beispielbilder": beispiel, "beispiel_text": "",
}
FA = {"stand": "04.11.2026", "levels": lv, "sources": sources, "persons": persons, "couples": couples, "timeline": timeline, "stories": stories, "fakten": fakten, "docs": docs,
      "ns": {}, "presse": presse, "research": research, "questions": questions, "fronts": {}, "backs": {}, "extra": {}, "orte": orte, "buch": buch}
open(os.path.join(HIER, "demo-hollenbeck.js"), "w", encoding="utf-8").write("/* Demo: erfundene Familie Hollenbeck. */\nwindow.FA = " + json.dumps(FA, ensure_ascii=False, indent=1) + ";\n")
print("ok")
