import re
from datetime import datetime

class DateFormatter:
    @staticmethod
    def parse_dates(date_str):
        """
        Parse a date string that may be a single date or a range, and return (start, end) in MM/DD/YYYY format.
        If only one date, end is empty string.
        """
        if not date_str:
            return ("", "")
        def clean_date(s):
            s = s.strip()
            s = re.sub(r"^[A-Za-z]{3,}, ", "", s)
            return s
        def to_mmddyyyy(s):
            for fmt in ("%b %d, %Y", "%B %d, %Y"):
                try:
                    return datetime.strptime(s, fmt).strftime("%m/%d/%Y")
                except Exception:
                    continue
            return s  # fallback: return as-is if parsing fails
        if '\u2014' in date_str:
            parts = date_str.split('\u2014')
            start_raw = clean_date(parts[0])
            end_raw = clean_date(parts[1])
            return (to_mmddyyyy(start_raw), to_mmddyyyy(end_raw))
        else:
            raw = clean_date(date_str)
            return (to_mmddyyyy(raw), "")

    @staticmethod
    def format_registration_open(date_str):
        """
        Convert 'Sat, Feb 21, 2026 at 6:53 AM' to 'MM/DD/YYYY - HH:MM'.
        If parsing fails, return the original string.
        """
        if not date_str:
            return ""
        s = date_str.strip()
        s = re.sub(r"^[A-Za-z]{3,}, ", "", s)
        for fmt in ("%b %d, %Y at %I:%M %p", "%B %d, %Y at %I:%M %p"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime("%m/%d/%Y - %H:%M")
            except Exception:
                continue
        return date_str

    @staticmethod
    def format_registration_date(date_str):
        """
        Convert 'Sat, Feb 21, 2026 at 6:53 AM' or 'Sat, Feb 21, 2026' to 'MM/DD/YYYY'.
        If parsing fails, return the original string.
        """
        if not date_str:
            return ""
        s = date_str.strip()
        s = re.sub(r"^[A-Za-z]{3,}, ", "", s)
        for fmt in ("%b %d, %Y at %I:%M %p", "%B %d, %Y at %I:%M %p", "%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(s, fmt).strftime("%m/%d/%Y")
            except Exception:
                continue
        return date_str
