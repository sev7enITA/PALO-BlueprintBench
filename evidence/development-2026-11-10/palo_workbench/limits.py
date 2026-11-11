"""Resource guardrails, not throughput qualification or model context limits."""
MAX_BYTES = 128 * 1024 * 1024
MAX_CASE_BYTES = 250 * 1024 * 1024
MAX_FILES = 10
MAX_PAGES = 2000
MAX_ROWS = 100000
MAX_COLUMNS = 200
MAX_UNITS = 250000
MAX_TEXT = 20000000
MAX_REQUEST = 4 * ((MAX_CASE_BYTES + 2) // 3) + 100000


def public():
    return dict(file_bytes=MAX_BYTES, case_bytes=MAX_CASE_BYTES, files=MAX_FILES,
                pdf_pages=MAX_PAGES, rows=MAX_ROWS, columns=MAX_COLUMNS,
                source_units=MAX_UNITS, text_characters=MAX_TEXT)
