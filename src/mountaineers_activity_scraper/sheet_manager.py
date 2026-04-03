import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

class SheetManager:
    def __init__(self, sheet_name, creds_file, headers):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(creds)
        self.ws = client.open(sheet_name).sheet1
        self.headers = headers
        self._ensure_headers()
        self.url_to_row = self._build_url_to_row()

    def _ensure_headers(self):
        all_rows = self.ws.get_all_values()
        if not all_rows or all_rows[0] != self.headers:
            self.ws.clear()
            self.ws.append_row(self.headers)

    def _build_url_to_row(self):
        all_rows = self.ws.get_all_values()
        return {row[0]: idx+2 for idx, row in enumerate(all_rows[1:]) if row}

    def write_row(self, row_data):
        url = row_data[0]
        last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        row_data_with_ts = row_data + [last_updated]
        def col_letter(n):
            result = ''
            while n > 0:
                n, rem = divmod(n - 1, 26)
                result = chr(65 + rem) + result
            return result
        num_cols = len(row_data_with_ts)
        start_col = 2  # B
        end_col = num_cols
        range_str = f"{col_letter(start_col)}{{row}}:{col_letter(end_col)}{{row}}"
        if url in self.url_to_row:
            row_num = self.url_to_row[url]
            self.ws.update(range_str.format(row=row_num), [row_data_with_ts[1:]])
            print(f"Updated: {url} at {last_updated}", flush=True)
        else:
            self.ws.append_row(row_data_with_ts)
            print(f"Added: {url} at {last_updated}", flush=True)
            # Refresh mapping to include new row
            self.url_to_row = self._build_url_to_row()