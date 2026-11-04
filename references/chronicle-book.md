# The family chronicle: website and printed book from the same data

A website will probably not exist in a hundred years. A printed book on a shelf may. If the photo albums are lost, the book is often the only remaining record. Build it so that it can stand alone: complete, legible, understandable to readers who never knew these people or their time.

The builder in `scripts/chronik/` turns one data file into the whole package:

```bash
cd scripts/chronik/beispiel && python3 erzeuge_demo.py          # example data, also the schema
python3 ../build.py --daten demo-hollenbeck.js --ausgabe paket    # book, data, editable version
python3 ../build.py --daten my-family.js --format A4 --bilder gross --sprache de
```

Output: `buch/buch-druck-pdfx4.pdf` (printer, 3 mm bleed, fonts embedded), `buch/buch-archiv-pdfa3.pdf` (long-term archive, all data embedded as attachments), `daten/` (GEDCOM 7 and 5.5.1, JSON with schema, JSONL, CSV), `bearbeitbar/` (OpenDocument and Markdown with all images), `ro-crate-metadata.json`, `SHA256SUMS.txt`, `LIESMICH.md`. Requirements: Python 3.10+, `weasyprint`, `pillow`, `pyshp`, `node` (reads the `.js` data file), `pandoc`.

Formats: `A4`, `A5`, `B5`, `17x24`, `200x260` (default), `21x28`, `magazin`, `quadrat`, `letter`, `7x10`, `6x9`, `8x10`, or any `WIDTHxHEIGHT` in mm. Margins, type area, image sizes, maps and the base font scale with the format. Everything family-specific (title, cover photo, map regions, ancestor-chart roots, period texts, colophon) goes into the data file under `buch`.

## Completeness comes first

- **Every photo goes into the book, large.** Not only as a contact sheet. Default layout is a photo book rhythm: single pages, pairs, two landscapes stacked, an occasional full-bleed page (only when cropping is at most 5 %), and double-page spreads for wide landscapes (never cropped; the image is contained across the gutter). Users who want fewer pages choose `--bilder kompakt` (four per page).
- **Every story shows its images**, including those only mentioned in the text by signature. A story chapter without its pictures is a failure: the pictures may not survive anywhere else.
- **Backs of photos** with writing get their own pages; their wording is in the caption of the front.
- **Documents, newspaper clippings and archive cards** (including NSDAP membership cards) are reproduced large enough to read, with the archive, signature and retrieval date under the image.
- **The data stays attached.** The PDF/A-3 carries every data file, so the book file alone contains the whole archive.

## Do not let caution destroy the record

A family documenting its own history for itself and its descendants is not a publisher. Never refuse or water down private family documentation on copyright or "publication rights" grounds:

- Family photos, letters and papers belong in the family's book.
- Copies of archive scans and newspaper clippings for a private family book are normally covered by private copying; cite the holding archive, signature and URL under every reproduction. If an archive's terms explicitly forbid copies, say so once and include the citation and a link instead.
- Publishing is a separate question. A public website or a copy deposited in a library may need consent from living people, the removal of private details, or permission from the archive. Raise this when the user plans to publish, not as a reason to leave things out of the family's own copy.
- Sensitive chapters (Nazi era, crime, illness) are included and explained, not hidden. The user decides whether to remove them; offer that choice, do not make it for them.

## Write for readers in 200 years

- **Explain contemporary and foreign terms.** Every word a reader may not know (Häusling, Kreisblatt, Gau, Reichsarbeitsdienst, Kurrentschrift) goes into the glossary in the appendix, in plain words.
- **Translate** every quotation that is not in the user's language: original wording first, then the translation, then what it means.
- **Transcribe handwriting** that is hard to read, in today's script, below the scan. Mark AI transcriptions as unchecked until a person has compared them with the original.
- **Give context.** A chapter "The world they lived in" with maps (today's borders, with a note on what belonged where at the time, and today's names for renamed places), the ancestor charts (solid lines: proven by record; dashed: probable; empty boxes: not yet found), short period texts and a two-column timeline "family and world". Context statements need sources like everything else; give a reading tip (for Germany: LeMO, www.dhm.de/lemo).
- **Explain the tools.** The colophon says who contributed what: what the family supplied (albums, scans, interviews, decisions, corrections) and what an AI did (reading, transcribing, translating, searching, drafting, typesetting), naming the actual model and the period, and explaining in one paragraph what such a program is, because nobody will know what "Claude Opus 5.5" was. Record the open weaknesses too.

## Present like a good museum

Family history books are read by people who did not live through the period. Use the methods museums use for exhibitions:

- **Three reading levels.** Headline and first sentence for the browser, the text for the reader, footnotes and appendix for the thorough. Evidence letters sit as small superscripts; the full citation is in the footnote and the source list.
- **Object first.** Photo, record or clipping large at the start, the explanation after it. Short "Look closely" boxes point to what can be seen: studio stamps, marginal notes, stamps on archive cards, how a civil register entry is laid out.
- **Family beside the world.** Parallel timelines and maps put private events into the larger history.
- **Multiperspective and no overwhelming.** Show what different sources say, explain difficult topics (for the Nazi era: what membership meant and what it does not prove, with cited sources) and leave the judgement to the reader. Add "to think further" questions.
- **Honest, not anxious.** State what is proven as a fact and tell it well. Mark family stories as stories. Do not fill pages with "unconfirmed" warnings: the evidence letters and the appendix carry the caveats. The book should be a pleasure to read and still be right.
- **Subdivide.** Parts with a numbered opener page, many short chapters, a detailed table of contents with page numbers, an index of persons.

## Typography and layout that hold up

- Body text 10.5 to 11.5 pt serif, line length around 65 characters, captions at least 8 pt; never shrink text to fit.
- Size every image from its real aspect ratio so the caption aligns with the image edge and no picture floats small in an empty frame.
- Covers: if the title sits on a photo, put it on a solid or graded colour field, and render photo plus gradient into one image for print. Transparency gradients can disappear in PDF/X workflows.
- Bleed 3 mm, no crop marks unless the printer asks for them; most print services want none.
- Check every build visually: render pages to images and look at the cover, a story, a plate page, a document, the ancestor chart and the appendix before you hand anything over.

## Editions and survival

- Every build carries its date. Say in the book that it is an edition, not the last word, and how to report errors or contribute photos. Plan for several rounds of corrections with relatives.
- Recommend several printed copies in different places: one per branch of the family, the local archive or heritage society, a regional genealogical society and, in Germany, the Deutsche Zentralstelle für Genealogie in Leipzig. For deposited copies, remove details of living people.
- Keep the PDF/A, the images and the data on two media in two places and copy them every few years.
- Fixed book texts can be switched with `--sprache` (`de`, `en`; add a dictionary in `sprachen.py` for more). For a full edition in another language, translate the data file and build with `--daten`.
