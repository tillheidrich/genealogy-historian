# Workflow, data and preservation

## 1. Securing the material

- Scan photos front and back, letters, documents, notes. 600 dpi for photos, 300–400 dpi for documents, lossless master files (TIFF or PNG), derived web copies.
- Give every item a stable ID (for example ARCHIVE-F0001 for photos, D0001 for documents). Write the ID on the sleeve, not on the object.
- Transcribe inscriptions on backs verbatim; note handwriting, stamps, studio names.
- Keep originals as they were found; record the original order (album, box, page).

## 2. Data model

Keep three linked lists:

- **People**: ID, names and variants, sex, events, relationships, photos, notes.
- **Events**: type (birth, baptism, marriage, death, burial, residence, occupation, military, migration, other), date (with precision: exact, about, before, after), place (historical and modern name), level, sources, confidence.
- **Sources**: ID, type, archive or owner, holding and signature, URL, date viewed, description, rights.

Add:

- **Research log**: date, question, where searched, query, result, follow-up.
- **Negative results**: as in method.md.
- **Open questions and tasks**: who does what (archive request, interview, visit).
- **Questions for witnesses**: linked to the people and documents they concern.

A plain JSON or spreadsheet file under version control is enough. Export to GEDCOM for exchange with genealogy software; keep the richer source data in your own format.

## 3. Changes

- Back up or version before every bulk change (for example a git tag).
- Never overwrite a statement silently. Keep the earlier version and the reason for the change.
- Corrections from family members are E until confirmed.

## 4. Archive requests

- One request per archive, with everything the archive needs (see archive-letters.md).
- Record the date sent, the reply, fees and results.

## 5. Publishing

- A private, access-controlled website works well for families: people, family sheet, timeline, map, photos with IDs, sources, open questions.
- Public pages only without living people's data.
- Show levels and sources on every page; let readers report corrections.

## 6. Long-term preservation

- A website does not last without someone paying and maintaining it. Make a preservation package as well:
  - PDF/A of all content,
  - GEDCOM of the tree,
  - full-resolution scans,
  - a plain-text README that explains the structure.
- Follow 3-2-1: three copies, two kinds of media, one off-site (for example a relative's drive).
- When the research is stable, print a book for the family. With an ISBN, legal deposit copies go to the national library (in Germany the Deutsche Nationalbibliothek), which keeps them permanently. A copy for the local or regional archive makes the family findable there.
- Freeze an edition ("edition 2027") rather than printing work in progress.
