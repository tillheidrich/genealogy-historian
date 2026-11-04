# Old newspapers and OCR

Local newspapers hold what registers do not: accidents, court cases, runaways, awards, obituaries, advertisements of craftsmen, internees and escapes. Full-text search makes them usable, but OCR of old print is error-prone.

## 1. Search strategy

- Search surname together with a place, as a proximity search (for example `"Name Place"~6` in Solr-based portals). A surname alone returns noise.
- Search variants: umlauts with and without (ü, u, ue), Fraktur misreadings (R/P, B/V, ck/k, ſ/f, rn/m), dropped or doubled letters, foreign spellings by foreign clerks and journalists.
- Search co-occurring names: once one article is found, search for the other people named in it (fellow prisoners, witnesses). Follow-up reports often name the same group.
- Search institutions and events, not only people (a camp name, a court, a firm).
- Restrict the period and the region when the portal allows it. If a filter breaks the API, drop it and filter the results yourself.

## 2. Reading hits

- Open the page scan, read the article fully, transcribe the relevant part exactly.
- Note paper, edition, date, page, section (for example "local news, Brest"), and the stable URL.
- Translate foreign-language articles and keep the original quote.
- Newspapers get ages, spellings and occupations wrong. Treat them as level Z and decide the match separately (identity-matching.md).
- Check whether the same report appeared in other editions or papers; regional editions differ.

## 3. Example of a good chain (anonymised)

A family story: "He ran away as a boy." Full-text search of the boy's surname and home town returns nothing; a proximity search of the stepfather's occupation and the town finds a 1902 report about a twelve-year-old "Ed. P.", stepson of a cartwright, picked up at a railway station 500 km away. The printed surname differs by one letter from the family name (P for R, a hearing or setting error); the stepfather's name and occupation match an address book. Result: very likely the ancestor, level Z.

## 4. Clippings

- Use the page's layout file (ALTO XML) to locate the text lines of the article and crop the page image to those coordinates, with a margin.
- Many portals offer images via IIIF: request only the region you need.
- Save the clipping with a stable name, keep the link to the full page and the citation beside it.
- If the image server blocks automated access, ask the user to open the page or save the image in their own browser. Never bypass the protection.

## 5. Courtesy and limits

- Respect rate limits. On HTTP 429 wait and slow down; do not hammer the server.
- Prefer official APIs and bulk interfaces over page scraping.
- Do not republish whole pages if the terms forbid it; a citation clipping with source is usually acceptable, but check.


## AI transcription of handwriting and print

- Read yourself first, then use the model. Give context: language, period, place, names you already know.
- Work in small pieces and compare word by word with the image. Check names, places, numbers and abbreviations separately.
- Language models make subtle, plausible errors; classic OCR and Transkribus make visible ones. Be more suspicious of fluent output.
- If a model returns fluent text for a passage you cannot read, treat that as a warning, not a success. Models have invented whole diary entries in Kurrent.
- Mark every AI reading as "read by AI, not checked" until a person has checked it.
- For hard pages, ask a community (for example r/Kurrent, FamilySearch Community, regional forums): send the whole entry with its header, place and year, and your own reading.
