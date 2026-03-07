# Account Registry (v1)

Authoritative list of known accounts and ownership labels for ETL mapping.

## Ownership Labels (Canonical)
- `Shai (Private)`
- `Shai & Nirit (Joint)`

## Banks
- `Bank Leumi` -> `Shai (Private)`
- `Bank Hapoalim` -> `Shai (Private)`
- `Mizrachi` -> `Shai & Nirit (Joint)`

## Credit Cards
- `Max Uniq` -> `Shai & Nirit (Joint)`
- `Isracard 4054` -> `Shai & Nirit (Joint)`
- `Mastercard 4779` -> `Shai (Private)`
- `Mastercard 7353` -> `Shai (Private)`

## Usage Rules
- Detectors/parsers should map incoming source files to one `Account` value above.
- Each normalized row must include one canonical `Ownership` value above.
- If a new account appears, append it here first, then update parser/detector rules.
