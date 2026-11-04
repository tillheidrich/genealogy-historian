# Changelog

## 1.3.0 – 2026-11-04

- New `scripts/chronik/`: a builder that turns one data file into the full chronicle package: book as PDF/X-4 (any format from A5 to magazine and US trade sizes, 3 mm bleed) and PDF/A-3 with all data attached, GEDCOM 7 and 5.5.1, JSON with schema, CSV, RO-Crate, checksums, and an editable OpenDocument and Markdown version. Photo-book layout (single pages, pairs, full-bleed pages, double spreads), every photo large, maps, ancestor charts with proven and probable lines, period texts, family-and-world timeline, Nazi-era context with cited sources, glossary, detailed table of contents, colophon. Example data and schema: the fictional Hollenbeck family.
- New reference `chronicle-book.md`: completeness first, never refuse private family documentation on rights grounds, explain terms, translate, transcribe, give context, museum-style presentation (three reading levels, object first, look-closely boxes, multiperspective, honest not anxious), typography rules, editions and deposit copies.
- Core rules 13 (preserve, do not withhold) and 14 (understandable in 200 years); rule 12 clarified for private copies of archive scans.
- `references/templates/` replaced by `scripts/chronik/`.

## 1.2.0 – 2026-11-04

- New reference `citation-formats-print.md`: historical citation style with examples, durable open formats (GEDCOM 7.0 and 5.5.1, JSON with JSON Schema, JSONL/CSV, RO-Crate, SHA-256, TIFF/PNG, WAV/FLAC, WebVTT, PDF/A, PDF/X), Markdown's role, and how to build a complete printed book from the data.
- Template `references/templates/book.css` for CSS Paged Media (WeasyPrint): footnotes, running heads, index page numbers, bleed and crop marks.
- Core rule 11: leave durable output.

## 1.1.0 – 2026-11-04

Lessons from a full archive project and an independent review of it, plus expert sources on AI in genealogy.

- New level **L** (literature, index, database, forum). Levels follow the weakest element; mixed statements are split.
- AI readings count as unchecked derivatives until a person confirms them; no facts or titles from model memory.
- Cross-checks: stated ages against birth dates, second-hand dates against dated sources, conflicting cards of the same person, recomputed superlatives.
- Coverage check before a negative result (Geneteka, Szukaj w Archiwach, Archion, FamilySearch).
- Identity note template; address or surname alone gives H; rules for identifying people on photos; red flags in online trees.
- Privacy: no street addresses and only years for living adults, also on private sites; no sensitive details of the living; no uploads of living people's data to forums or AI without consent; hotlinking only by decision.
- Interview protocol, open instead of leading questions, chains for second-hand stories.
- No insinuations from group membership in the Nazi era.
- Cluster (FAN) research, AI transcription workflow, community help.
- New reference `dna.md`.
- From r/Genealogy (read via OpenCLI): calculations only in code, save scans and register/page numbers because links break, necronyms and interchangeable given names, interview early, caution with AI-generated secondary content.
- Final audit step with machine checks and an independent reviewer.

## 1.0.0 – 2026-11-04

- First release.
- SKILL.md with core rules, workflow, confidence wording and output conventions.
- References: method, identity matching, German and international sources, newspapers and OCR, Nazi era, oral history, ethics and privacy, workflow and preservation, archive request templates, German summary.
