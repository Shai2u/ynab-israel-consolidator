"""Max Uniq-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
MAX_UNIQ_ACCOUNT_NAME = "Max Uniq"

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
MAX_UNIQ_INPUT_DATE_FORMAT = "%d-%m-%Y"

# Default header row index fallback in Max Uniq exports.
MAX_UNIQ_HEADER_DEFAULT_ROW_IDX = 3

# Header signature used to detect the true header row.
MAX_UNIQ_REQUIRED_HEADERS: set[str] = {
    "תאריך עסקה",
    "שם בית העסק",
    "קטגוריה",
    "סוג עסקה",
    "מטבע חיוב",
    "מטבע עסקה מקורי",
    "תאריך חיוב",
    "הערות",
    "אופן ביצוע ההעסקה",
    "שער המרה ממטבע מקור/התחשבנות לש\"ח",
}

# Fill this with source header mappings once discovered.
MAX_UNIQ_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {'תאריך עסקה': 'Date',
                                                          'שם בית העסק': 'Payee',
                                                          'סכום חיוב': 'Amount',
        
                                                          'סכום עסקה מקורי': 'Original_amount',
                                                          'קטגוריה': 'Category_temp',
                                                          'סוג עסקה': 'Type_of_transaction',
                                                          'מטבע חיוב': 'Currency_of_charge',
                                                          'מטבע עסקה מקורי': 'Original_currency',
                                                          'תאריך חיוב': 'Date_of_charge',
                                                          'הערות': 'Memo_temp',
                                                          'אופן ביצוע ההעסקה': 'Method_of_execution',
                                                          'תיוגים': 'Tags',
                                                          'מועדון הנחות': 'Discount_club',
                                                          'שער המרה ממטבע מקור/התחשבנות לש\"ח': 'Exchange_rate'}
MAX_UNIQ_DICT_COLS = {'Method_of_execution': 'Method', 'Original_amount': 'Original Amount', 'Category_temp': 'Category', 'Currency_of_charge': 'Currency', 'Original_currency': 'Orig Currency', 'Type_of_transaction': 'Type', 'Date_of_charge': 'Date of Charge', 'Tags': 'Tags', 'Discount_club': 'Discount', 'Exchange_rate': 'Exchange Rate', 'Memo_temp':'Memo_temp'}
