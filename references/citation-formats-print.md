# Citation, durable data formats and the printed book

A website will not survive a century. A well-made book and a few plain files might. Build every archive so that it can be printed and re-read without the software that made it.

## 1. Citation

Use a full citation the first time a source appears, a short form afterwards, and a source list at the end. A reader in 50 years must find the record without the website.

Order for archival sources (German historical convention, compatible with Evidence Explained):

1. Holding institution, department (Landesarchiv NRW, Abteilung Rheinland)
2. Holding or fonds and signature (PA 3103 Nr. 601)
3. Description of the item (Standesamt Siersdorf, Sterberegister 1921, Nr. 35)
4. Exact location in the item (Bild 39; fol. 12r; S. 4)
5. For online images: URL and date viewed

Examples:

- Register: Landesarchiv Beispielland, Abt. Musterstadt, PA 0000 Nr. 000: Standesamt Musterdorf, Sterberegister 1921, Nr. 35 (Erika Beispiel geb. Muster), Bild 39, online eingesehen am TT.MM.JJJJ. (erfundenes Beispiel)
- Newspaper: Musterstädter Anzeiger, 26.06.1915, S. 3, Rubrik „Aus der Stadt“, Digitalisat ark:/00000/beispiel, eingesehen am TT.MM.JJJJ. (erfundenes Beispiel)
- Card file: Bundesarchiv, Bestand und Signatur, Karteikarte Max Mustermann, geb. 01.01.1900; Quelle des Scans, abgerufen am TT.MM.JJJJ. (erfundenes Beispiel; Karteien mit NS-Bezug nie mit echten Namen in öffentlichen Dateien)
- Family item: Familienarchiv Beispiel (Privatbesitz), Foto DFA-BSP-F0001, Rückseite, Bleistift. (erfundenes Beispiel)
- Interview: Erika Beispiel, Gespräch mit der Bearbeiterin, TT.MM.JJJJ, Tonaufnahme Q01, ab 01:21. (erfundenes Beispiel)
- Literature: Nachname, Vorname: Titel des Buches, 2. Aufl., Ort Jahr, S. … (erfundenes Beispiel)
- Forum or website: author or handle, title of the post, site, date of post, URL, date viewed. Mark it as level L.

Rules:

- Give persistent identifiers where they exist (ARK, DOI, URN, archive signature) in preference to search URLs.
- Record register, page and entry number even when you also store a link. Links break; signatures rarely do.
- Generate citations from structured source records (institution, holding, signature, item, location, url, date viewed), not by hand, so they stay consistent.

## 2. Durable data formats

Keep one structured master and derive everything else from it. Recommended set:

| Purpose | Format | Why |
|---|---|---|
| Family tree for other programs | GEDCOM 7.0 (FamilySearch, open standard since 2021), plus GEDCOM 5.5.1 for older software | Read by Gramps, Ancestris and most genealogy programs |
| Complete data | JSON with a JSON Schema describing every field | Plain text, self-describing, easy for people and AI to read |
| One statement per line | JSONL and CSV (UTF-8, semicolon) | Opens in any spreadsheet, diff-friendly |
| Package description | RO-Crate 1.1 (JSON-LD) | Recognised by research data archives; lists every file |
| Integrity | SHA-256 checksums | Detects silent damage when copying |
| Images | Masters as TIFF or PNG (lossless); access copies as JPEG or WebP; file name contains the signature | TIFF/PNG are archival standards |
| Audio and transcripts | WAV or FLAC masters; transcripts as plain text or WebVTT with time codes | Open, long-lived |
| Documents and the book | PDF/A for archiving (PDF/A-3 can embed the data files), PDF/X-4 for printing | ISO standards for preservation and print |
| Notes for people and AI | Markdown | Plain text, readable in 100 years without software |

Markdown is still the right choice for human-readable notes and for instructions to AI tools; it is plain text. It is not a database: keep facts in the structured master, not only in prose.

Storing level and confidence: in GEDCOM use QUAY (3 primary record, 2 secondary or print, 1 family or literature, 0 hypothesis or open) and repeat the level and confidence in a NOTE, because QUAY alone loses the distinction.

Privacy in exports: living people with years only and the RESN PRIVACY tag; no street addresses.

## 3. The printed book

Aim for a book that is complete on its own: someone who has only the book must be able to follow every claim to its source.

Contents, in this order:

1. Title page and imprint (who compiled it, when, with which tools, rights, privacy rule, where the digital data is).
2. How to read the book (levels, confidence, what an asterisk means).
3. People by generation: life dates, every statement with level, confidence and a footnote.
4. Stories, each with its evidence paragraph.
5. Finds in newspapers and archives: original wording, translation, interpretation, source.
6. Timeline.
7. State of research: negative results, open tasks, questions for the family, research log.
8. Source list with full citations.
9. Index of persons with page numbers (and places, if useful).
10. About the data: which files exist and how to open them.

Production:

- Write the book from the same structured data as the website. Never edit the PDF by hand; fix the data and rebuild.
- Use CSS Paged Media (for example WeasyPrint) or LaTeX. With WeasyPrint: `pdf/x-4` for the printer, with `bleed: 3mm; marks: crop cross;` and a trim size the printer offers (for example 170 × 240 mm); `pdf/a-3b` for the archive copy, with the data files attached.
- Footnotes for sources (`float: footnote`), running heads, page numbers, page references in the index (`target-counter`).
- Fonts: embed open-licensed fonts (SIL OFL), for example Source Serif 4 for text and a sans serif for headings. Body text 9.5 to 10.5 pt.
- Images: 300 dpi at print size; give each figure its signature.
- Check the PDF before sending: page count, bleed and trim boxes, fonts embedded, images resolved, no placeholder text. Ask the printer for their PDF/X profile and colour requirements; some want CMYK with a specific output intent.
- Print on ageing-resistant paper (ISO 9706) if the printer offers it.
- Keep at least: the printed book, the PDF/A file and the image masters on two media in two places, copied to new media every few years.

The complete builder (stylesheet, maps, ancestor charts, layout rules) is in `scripts/chronik/`; see `references/chronicle-book.md`.
