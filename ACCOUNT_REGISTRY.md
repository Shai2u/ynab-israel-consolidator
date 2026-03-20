# Account Registry (v1)

Authoritative list of known accounts, ownership labels, and linked settlement banks for ETL mapping.

## Ownership Labels (Canonical)
- `Shai (Private)`
- `Shai & Nirit (Joint)`

## Banks
- `Bank Leumi` -> `Shai (Private)`
- `Bank Hapoalim` -> `Shai (Private)`
- `Mizrachi` -> `Shai & Nirit (Joint)`

## Credit Cards
- `Max Uniq` -> `Shai & Nirit (Joint)` (linked bank: `Mizrachi`)
- `Isracard 4054` -> `Shai & Nirit (Joint)` (linked bank: `Mizrachi`)
- `Mastercard 4779` -> `Shai (Private)` (linked bank: `Bank Hapoalim`)
- `Mastercard 7353` -> `Shai (Private)` (linked bank: `Bank Leumi`)

## Usage Rules
- Detectors/parsers should map incoming source files to one `Account` value above.
- Each normalized row must include one canonical `Ownership` value above.
- Credit-card accounts should also map to one linked settlement bank account.
- If a new account appears, append it here first, then update parser/detector rules.
