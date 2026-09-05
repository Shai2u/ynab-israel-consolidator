"""Mastercard 4779-specific parsing and mapping constants (prototype)."""

# Last-4 detector value -> canonical Visa Cal account name.
VISA_CAL_LAST4_TO_ACCOUNT_NAME: dict[str, str] = {
    "4779": "Mastercard_4779_private",
    "7353": "Mastercard_7353_private",
}

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
VISA_CAL_INPUT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Header cells common to every known Visa Cal export variant (full detail,
# 90-day, and billing-cycle). Values are raw, pre-translate_columns cell text
# (embedded newlines and all), since header detection runs before newlines
# are stripped. Used to skip past summary/banner rows that some exports
# (e.g. the billing-cycle "cal_<last4>_<mmyy>.xlsx" export) prepend before
# the real header row.
VISA_CAL_REQUIRED_HEADERS: set[str] = {'תאריך\nעסקה', 'שם בית עסק', 'הערות'}

# Fill this with source header mappings once discovered.
# 'סכום עסקה' and 'סכום חיוב' only appear in the billing-cycle export variant,
# which splits amount into transaction-time amount and billed amount (blank
# while a charge is still pending) instead of the single 'סכום בש"ח' column
# used by the full-detail/90-day exports. coalesce_amount_columns() in
# card_visa_cal_proto.py merges whichever pair is present back into Amount.
VISA_CAL_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {'סוג עסקה': 'Type_of_transaction',
                                                          'מועד חיוב': 'Date_of_charge',
                                                          'סכום בש"ח': 'Amount',
                                                          'סכום עסקה': 'Amount_transaction',
                                                          'סכום חיוב': 'Amount_billed',
                                                          'ענף': 'Branch_category',
                                                          'שם בית עסק': 'Payee',
                                                          'פרטי חיוב': 'Details',
                                                          'תאריך עסקה': 'Date',
                                                          'הערות': 'Memo_temp',
                                                          'הנחה': 'Discount'}
VISA_CAL_DICT_COLS = {'Type_of_transaction': 'Type', 'Date_of_charge': 'Date of Charge', 'Details': 'Details', 'Branch_category': 'Category', 'Memo_temp': 'Memo', 'Discount': 'Discount'}
