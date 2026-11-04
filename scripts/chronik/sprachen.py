"""Feste Buchtexte in weiteren Sprachen. Der Inhalt selbst kommt aus der Datendatei (--daten),
die für eine fremdsprachige Ausgabe vollständig übersetzt vorliegen muss (die KI kann das übernehmen).
Neue Sprache: ein weiteres Wörterbuch eintragen, Schlüssel ist der deutsche Text."""
UI = {
 "en": {
  "Inhalt": "Contents", "Bevor es losgeht": "Before we begin", "Die Welt, in der sie lebten": "The world they lived in",
  "Karten, Zeitabschnitte und der Stammbaum: der Rahmen für alles, was folgt.": "Maps, periods and the family tree: the frame for everything that follows.",
  "Die Geschichten": "The stories", "Was die Familie erzählt und was die Quellen dazu sagen.": "What the family tells, and what the sources say.",
  "Fakten und Zusammenhänge": "Facts and connections", "Was wir sicher wissen, was überrascht und wie wir es herausgefunden haben.": "What we know for certain, what surprised us, and how we found out.",
  "Bilder": "Pictures", "Die Fotos aus den Alben, groß und mit dem, was auf ihren Rückseiten steht.": "The photographs from the albums, large, with what is written on their backs.",
  "Urkunden und Briefe": "Records and letters", "Standesamtsregister und Archivpost, mit Abschrift und Erklärung.": "Civil registers and archive letters, with transcription and explanation.",
  "Die NS-Zeit": "The Nazi era", "Die Karteikarten der NSDAP-Mitgliederkartei, lesbar und eingeordnet.": "The cards of the Nazi party membership file, legible and explained.",
  "Die Menschen": "The people", "Alle Personen nach Generationen, mit Lebensdaten und Belegen.": "Everyone, by generation, with dates and evidence.",
  "Funde in Zeitungen und Archiven": "Finds in newspapers and archives", "Zeitungsmeldungen im Wortlaut, übersetzt und eingeordnet.": "Newspaper items in the original wording, translated and explained.",
  "Zeitleiste": "Timeline", "Zweihundert Jahre in einer Liste.": "Two hundred years in one list.",
  "Für Genaue": "For the thorough", "Belegstufen, Begriffe, Quellen, offene Fragen, Personenregister und das ganze Fotoarchiv.": "Evidence levels, terms, sources, open questions, index of persons and the whole photo archive.",
  "Wo sie lebten": "Where they lived", "Das Aachener Revier": "The Aachen coalfield", "Familie und Welt": "Family and world",
  "In der Familie": "In the family", "In der Welt": "In the world", "Worauf das beruht": "What this is based on", "Wie wir das wissen": "How we know",
  "Wortlaut": "Original wording", "Auf Deutsch und eingeordnet": "Translated and explained", "Abschrift": "Transcription", "Was der Eintrag sagt": "What the entry says",
  "Rückseite": "Back", "Begriffe": "Terms", "Quellen": "Sources", "Personen": "Index of persons", "Zu den Daten": "About the data",
  "Wie dieses Buch entstand": "How this book was made", "Wie es weitergehen kann": "How the research can continue", "Das ganze Fotoarchiv": "The whole photo archive",
  "Weitere Fotos aus den Alben": "More photographs from the albums", "Die Rückseiten": "The backs", "Belegstufen und Sicherheit": "Evidence levels and certainty",
  "Genau hinsehen.": "Look closely.", "Zum Weiterdenken.": "To think further.", "noch nicht gefunden": "not yet found", "Was die NSDAP war": "What the Nazi party was",
  "So liest man einen Registereintrag": "How to read a civil register entry", "Die Karten dieser Familie": "This family's cards", "Anhang": "Appendix",
 }
}
PRAEFIX = {"en": {"Die Vorfahren von ": "The ancestors of ", "Weitere Fotos": "More photographs", "Urgroßeltern von ": "Great-grandparents of ",
                  "Großeltern von ": "Grandparents of ", "Eltern von ": "Parents of ", "Kinder von ": "Children of "}}
def uebersetze(html_text, sprache):
    d = UI.get(sprache)
    if not d:
        return html_text
    import re
    for de, x in PRAEFIX.get(sprache, {}).items():
        html_text = re.sub(r"(>\s*)" + re.escape(de), lambda m: m.group(1) + x, html_text)
    for de in sorted(d, key=len, reverse=True):
        html_text = re.sub(r"(>\s*)" + re.escape(de) + r"(\s*<)", lambda m: m.group(1) + d[de] + m.group(2), html_text)
    return html_text
