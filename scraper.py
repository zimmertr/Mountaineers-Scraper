import argparse
import requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime
import re


def scrape_element_text(soup, element, class_name=None, find_child=None, skip_label=False):
    try:
        el = soup.find(element, class_=class_name) if class_name else soup.find(element)
        if el and find_child:
            el = el.find(find_child)
        if el:
            if skip_label:
                label = el.find("label")
                if label:
                    label.decompose()
            return el.get_text(strip=True)
        return ""
    except Exception as e:
        print(f"Failed to scrape {element}.{class_name}: {e}", flush=True)
        return ""


def scrape_date_range(soup):
    try:
        details = soup.find("ul", class_="details")
        if details:
            first_li = details.find("li")
            if first_li:
                text = first_li.get_text(strip=True)
                text = " ".join(text.split())
                return text
        return ""
    except Exception as e:
        print(f"Failed to scrape date: {e}", flush=True)
        return ""


def scrape_primary_leader(soup):
    try:
        roster = soup.find("div", class_="roster-contact")
        if roster:
            leader_name = ""
            for div in roster.find_all("div"):
                if "roster" not in div.get("class", []):
                    text = div.get_text(strip=True)
                    if text:
                        leader_name = text
                        break
            position = roster.find("div", class_="roster-position")
            if position:
                pos_text = position.get_text(strip=True)
                if leader_name:
                    leader_name = f"{leader_name} ({pos_text})"
                else:
                    leader_name = pos_text
            # Strip "(Primary Leader)" from cell data
            leader_name = leader_name.replace("(Primary Leader)", "").strip()
            return leader_name
        return ""
    except Exception as e:
        print(f"Failed to scrape leader: {e}", flush=True)
        return ""


def scrape_from_ul_details(soup, label_text, tag_type="label", extract_tag=None):
    try:
        all_details = soup.find_all("ul", class_="details")
        for details in all_details:
            for li in details.find_all("li"):
                tag = li.find(tag_type)
                if tag and label_text in tag.get_text():
                    if extract_tag:
                        extracted = li.find(extract_tag)
                        if extracted:
                            text = extracted.get_text(strip=True)
                        else:
                            continue
                    else:
                        text = li.get_text(strip=True)
                        label_text_clean = tag.get_text(strip=True)
                        text = text.replace(label_text_clean, "").strip()
                    if label_text in ["Mileage", "Elevation Gain"]:
                        text = text.replace(" mi", "").replace(" ft", "").strip()
                    return " ".join(text.split())
        return ""
    except Exception as e:
        print(f"Failed to scrape '{label_text}': {e}", flush=True)
        return ""


def read_urls(filename):
    try:
        with open(filename) as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File not found: {filename}", flush=True)
        return []


def write_row(ws, row_data, url_to_row):
    """Write a single row with a timestamp calculated when processed"""
    url = row_data[0]
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_data_with_ts = row_data + [last_updated]
    # Dynamically calculate the correct range
    def col_letter(n):
        result = ''
        while n > 0:
            n, rem = divmod(n - 1, 26)
            result = chr(65 + rem) + result
        return result
    num_cols = len(row_data_with_ts)
    start_col = 2  # B
    end_col = num_cols  # e.g., Q for 17 columns
    range_str = f"{col_letter(start_col)}{{row}}:{col_letter(end_col)}{{row}}"
    if url in url_to_row:
        row_num = url_to_row[url]
        ws.update(range_str.format(row=row_num), [row_data_with_ts[1:]])
        print(f"Updated: {url} at {last_updated}", flush=True)
    else:
        ws.append_row(row_data_with_ts)
        print(f"Added: {url} at {last_updated}", flush=True)
        # Refresh mapping to include new row
        all_rows = ws.get_all_values()
        url_to_row.clear()
        for idx, row in enumerate(all_rows[1:], start=2):
            if row:
                url_to_row[row[0]] = idx


def parse_dates(date_str):
    """
    Parse a date string that may be a single date or a range, and return (start, end) in MM/DD/YYYY format.
    If only one date, end is empty string.
    """
    from datetime import datetime
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
    if '—' in date_str:
        parts = date_str.split('—')
        start_raw = clean_date(parts[0])
        end_raw = clean_date(parts[1])
        return (to_mmddyyyy(start_raw), to_mmddyyyy(end_raw))
    else:
        raw = clean_date(date_str)
        return (to_mmddyyyy(raw), "")


def format_registration_open(date_str):
    """
    Convert 'Sat, Feb 21, 2026 at 6:53 AM' to 'MM/DD/YYYY - HH:MM'.
    If parsing fails, return the original string.
    """
    from datetime import datetime
    if not date_str:
        return ""
    # Remove day of week
    import re
    s = date_str.strip()
    s = re.sub(r"^[A-Za-z]{3,}, ", "", s)
    # Try to parse
    for fmt in ("%b %d, %Y at %I:%M %p", "%B %d, %Y at %I:%M %p"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%m/%d/%Y - %H:%M")
        except Exception:
            continue
    return date_str


def format_registration_date(date_str):
    """
    Convert 'Sat, Feb 21, 2026 at 6:53 AM' or 'Sat, Feb 21, 2026' to 'MM/DD/YYYY'.
    If parsing fails, return the original string.
    """
    from datetime import datetime
    if not date_str:
        return ""
    import re
    s = date_str.strip()
    s = re.sub(r"^[A-Za-z]{3,}, ", "", s)
    # Try to parse with and without time
    for fmt in ("%b %d, %Y at %I:%M %p", "%B %d, %Y at %I:%M %p", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%m/%d/%Y")
        except Exception:
            continue
    return date_str


def build_row(soup, url):
    raw_name = scrape_element_text(soup, "h1")
    type_name = ""
    clean_name = raw_name
    if " - " in raw_name:
        type_name, clean_name = raw_name.split(" - ", 1)
    date_str = scrape_date_range(soup)
    start_date, end_date = parse_dates(date_str)
    reg_open = scrape_from_ul_details(soup, "Registration Open", tag_type="label")
    reg_open_fmt = format_registration_open(reg_open)
    reg_closed = scrape_from_ul_details(soup, "Registration Closed", tag_type="label")
    reg_closed_fmt = format_registration_open(reg_closed)
    reg_nonpriority = scrape_from_ul_details(soup, "Non-Priority Registration Open", tag_type="label")
    reg_nonpriority_fmt = format_registration_date(reg_nonpriority)
    return [
        url,
        type_name,
        clean_name,
        scrape_element_text(soup, "p", "documentDescription"),
        scrape_primary_leader(soup),
        start_date,
        end_date,
        scrape_from_ul_details(soup, "Committee", tag_type="label", extract_tag="a"),
        reg_open_fmt,
        reg_nonpriority_fmt,
        reg_closed_fmt,
        scrape_from_ul_details(soup, "Mileage", tag_type="strong", extract_tag="span"),
        scrape_from_ul_details(soup, "Elevation Gain", tag_type="strong", extract_tag="span"),
        scrape_from_ul_details(soup, "Availability", tag_type="label").split("(")[0].strip(),
        scrape_from_ul_details(soup, "Availability", tag_type="label", extract_tag="span"),
        scrape_element_text(soup, "div", "content-text", find_child="div", skip_label=True)
    ]


def main():
    parser = argparse.ArgumentParser(description="Scrape trip data and write to Google Sheet")
    parser.add_argument("--file", required=True, help="Text file with URLs")
    parser.add_argument("--sheet", required=True, help="Google Sheet name")
    parser.add_argument("--creds", required=True, help="Service account JSON file")
    args = parser.parse_args()

    urls = read_urls(args.file)
    if not urls:
        print("No URLs found", flush=True)
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(args.creds, scopes=scopes)
    client = gspread.authorize(creds)
    ws = client.open(args.sheet).sheet1

    HEADERS = [
        "URL", "Type", "Name", "Description", "Leader", "Start Date", "End Date", "Committee",
        "Registration Open", "Non-Priority Registration Open", "Registration Closed",
        "Mileage", "Elevation Gain", "Availability", "Capacity", "Leader's Notes",
        "Last Updated (UTC)"
    ]

    # Ensure header exists
    all_rows = ws.get_all_values()
    if not all_rows or all_rows[0] != HEADERS:
        ws.clear()
        ws.append_row(HEADERS)
        all_rows = [HEADERS]

    url_to_row = {row[0]: idx+2 for idx, row in enumerate(all_rows[1:]) if row}

    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{len(urls)}] Processing: {url}", flush=True)
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            row_data = build_row(soup, url)

            write_row(ws, row_data, url_to_row)
            time.sleep(1)  # rate limit

        except Exception as e:
            print(f"Failed to process {url}: {e}", flush=True)


if __name__ == "__main__":
    main()