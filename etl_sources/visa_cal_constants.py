"""Mastercard 4779-specific parsing and mapping constants (prototype)."""

# Last-4 detector value -> canonical Visa Cal account name.
VISA_CAL_LAST4_TO_ACCOUNT_NAME: dict[str, str] = {
    "4779": "Mastercard_4779_private",
    "7353": "Mastercard_7353_private",
}

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
VISA_CAL_INPUT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Fill this with required header values for header row detection.
VISA_CAL_REQUIRED_HEADERS: set[str] = set()

# Fill this with source header mappings once discovered.
VISA_CAL_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {'סוג עסקה': 'Type_of_transaction',
                                                          'מועד חיוב': 'Date_of_charge',
                                                          'סכום בש"ח': 'Amount',
                                                          'שם בית עסק': 'Payee',
                                                          'פרטי חיוב': 'Details',
                                                          'תאריך עסקה': 'Date',
                                                          'הערות': 'Memo_temp',
                                                          'הנחה': 'Discount'}
VISA_CAL_DICT_COLS = {'Type_of_transaction': 'Type', 'Date_of_charge': 'Date of Charge', 'Details': 'Details', 'Memo_temp': 'Memo', 'Discount': 'Discount'}
