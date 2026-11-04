# genealogy-historian

**Deutsch** · [English](#english)

Ein Skill für KI-Assistenten (Claude, Claude Code und andere Agenten), der Familienforschung so angeht, wie es eine Historikerin oder ein Historiker täte: mit Quellenkritik, Fundstellen zu jeder Aussage, offen ausgewiesener Unsicherheit und dokumentierten Negativbefunden.

## Wofür

- Ahnenforschung, Stammbaum, Familienarchiv
- Suche in Kirchenbüchern, Standesamtsregistern, Zeitungen, Adressbüchern, Militär- und Gefangenenakten
- Familienerzählungen prüfen
- Vorfahren in der NS-Zeit, sachlich und verantwortungsvoll
- Archivanfragen schreiben

Er funktioniert international und ist für deutsche und mitteleuropäische Quellen besonders ausführlich: Standesämter, Kirchenbücher, Landesarchive, Bundesarchiv, Zeitungsportal der Deutschen Digitalen Bibliothek, Schlesien und das heutige Polen.

## Grundsätze

1. Jede Aussage hat eine Fundstelle.
2. Belegstufe und Wahrscheinlichkeit stehen dabei.
3. Gelesen wird das Original, nicht der Suchtreffer.
4. Negativbefunde werden festgehalten.
5. Widersprüche bleiben sichtbar.
6. Lücken werden nicht mit Plausiblem gefüllt.
7. Familienerzählungen gelten als Hypothesen.
8. Lebende werden geschützt.

Die Kurzfassung steht in [references/kurzfassung-de.md](references/kurzfassung-de.md).

## Installation

- **Claude Code**: Ordner nach `~/.claude/skills/genealogy-historian/` kopieren (oder in `.claude/skills/` eines Projekts).
- **Claude.ai**: Ordner als ZIP packen und unter Einstellungen → Fähigkeiten (Skills) hochladen.
- **Andere Agenten**: `SKILL.md` als Anweisung laden; die Dateien in `references/` bei Bedarf nachlesen lassen.

## Aufbau

| Datei | Inhalt |
|---|---|
| `SKILL.md` | Kernregeln und Arbeitsablauf |
| `references/method.md` | Quellenkritik, Beweisstandard, Belegstufen, Widersprüche |
| `references/identity-matching.md` | Gehört der Treffer zu unserer Person? |
| `references/sources-de.md` | Deutsche und mitteleuropäische Quellen, Sperrfristen |
| `references/sources-international.md` | Internationale Archive und Zeitungen |
| `references/newspapers-ocr.md` | Volltextsuche, Fraktur-OCR, Ausschnitte |
| `references/ns-era.md` | NS-Zeit |
| `references/oral-history.md` | Erzählungen und Interviews |
| `references/ethics-privacy.md` | Datenschutz, Rechte, Zugang |
| `references/workflow.md` | Inventar, Datenmodell, Backup, Veröffentlichung, Langzeitarchiv |
| `references/archive-letters.md` | Musteranfragen DE/EN |
| `references/dna.md` | DNA-Tests: Matches, cM, Ethnizitätsschätzung, Datenschutz der Verwandten |
| `references/kurzfassung-de.md` | Die Kernregeln auf Deutsch |

## Herkunft

Ein Projekt von [Heidrich Digital](https://heidrich-digital.de) (Till Heidrich), entstanden aus der Arbeit am eigenen Familienarchiv. Mehr dazu, Workshops und Auftragsarbeit: [dasfamilienarchiv.de](https://dasfamilienarchiv.de).

Fehler, Ergänzungen, weitere Quellen: gern als Issue oder Pull Request.

## Lizenz

Texte unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.de). Siehe [LICENSE](LICENSE).

---

## English

A skill for AI assistants (Claude, Claude Code and other agents) that approaches family history the way a trained historian would: source criticism, a citation for every claim, explicit uncertainty and documented negative results.

### Use it for

- ancestry research, family trees, family archives
- searching church books, civil registers, newspapers, city directories, military and prisoner records
- testing family stories
- ancestors in the Nazi era, factually and responsibly
- writing archive requests

It works internationally and is especially detailed for German and Central European sources: civil registries, church books, state archives, the German Federal Archives, the newspaper portal of the Deutsche Digitale Bibliothek, Silesia and today's Poland.

### Principles

1. Every claim has a citation.
2. Every claim carries an evidence level and a confidence.
3. Read the original, not the search hit.
4. Record negative results.
5. Keep contradictions visible.
6. Never fill gaps with plausible inventions.
7. Treat family stories as hypotheses.
8. Protect living people.

### Installation

- **Claude Code**: copy the folder to `~/.claude/skills/genealogy-historian/` (or a project's `.claude/skills/`).
- **Claude.ai**: zip the folder and upload it under Settings → Capabilities (Skills).
- **Other agents**: load `SKILL.md` as instructions and let the agent read `references/` as needed.

### Origin

A project by [Heidrich Digital](https://heidrich-digital.de) (Till Heidrich), built from work on his own family archive. Workshops and commissioned research: [dasfamilienarchiv.de](https://dasfamilienarchiv.de).

Corrections, additions and further sources are welcome as issues or pull requests.

### Licence

Text under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [LICENSE](LICENSE).
