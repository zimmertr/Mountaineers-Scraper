import argparse
import requests
import csv
import os
from .sheet_manager import SheetManager
import time
from datetime import datetime
from .date_utils import DateFormatter
from .scraper_utils import Scraper


def read_urls(filename):
    try:
        with open(filename) as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File not found: {filename}", flush=True)
        return []


def build_row(html, url):
    scraper = Scraper(html)
    raw_name = scraper.scrape_element_text("h1")
    type_name = ""
    clean_name = raw_name
    if " - " in raw_name:
        type_name, clean_name = raw_name.split(" - ", 1)
    date_str = scraper.scrape_date_range()
    start_date, end_date = DateFormatter.parse_dates(date_str)
    reg_open = scraper.scrape_from_ul_details("Registration Open", tag_type="label")
    reg_open_fmt = DateFormatter.format_registration_open(reg_open)
    reg_closed = scraper.scrape_from_ul_details("Registration Closed", tag_type="label")
    reg_closed_fmt = DateFormatter.format_registration_open(reg_closed)
    reg_nonpriority = scraper.scrape_from_ul_details("Non-Priority Registration Open", tag_type="label")
    reg_nonpriority_fmt = DateFormatter.format_registration_date(reg_nonpriority)
    return [
        url,
        type_name,
        clean_name,
        scraper.scrape_element_text("p", "documentDescription"),
        scraper.scrape_primary_leader(),
        start_date,
        end_date,
        scraper.scrape_from_ul_details("Committee", tag_type="label", extract_tag="a"),
        reg_open_fmt,
        reg_nonpriority_fmt,
        reg_closed_fmt,
        scraper.scrape_from_ul_details("Mileage", tag_type="strong", extract_tag="span"),
        scraper.scrape_from_ul_details("Elevation Gain", tag_type="strong", extract_tag="span"),
        scraper.scrape_from_ul_details("Availability", tag_type="label").split("(")[0].strip(),
        scraper.scrape_from_ul_details("Availability", tag_type="label", extract_tag="span"),
        scraper.scrape_element_text("div", "content-text", find_child="div", skip_label=True)
    ]


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape trip data and output to Google Sheet and/or CSV")
    parser.add_argument("--file", required=True, help="Text file with URLs")
    parser.add_argument("--output", choices=["csv", "google-sheets", "both"], default="csv", help="Output destination: csv (default), google-sheets, or both")
    parser.add_argument("--output-file-name", default="output.csv", help="CSV output file name (default: output.csv)")
    parser.add_argument("--sheet", help="Google Sheet name (required if output is google-sheets or both)")
    parser.add_argument("--creds", help="Service account JSON file (required if output is google-sheets or both)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    return parser.parse_args()

def collect_rows(urls, headers, delay=1.0):
    rows = []
    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{len(urls)}] Processing: {url}", flush=True)
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            row_data = build_row(resp.text, url)
            last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            row_data.append(last_updated)
            rows.append(row_data)
        except Exception as e:
            print(f"Failed to process {url}: {e}", flush=True)
        time.sleep(delay)
    return rows

def write_csv(csv_path, headers, rows):
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"CSV written to {csv_path}")

def upload_to_sheets(sheet_name, creds, headers, rows):
    sheet_manager = SheetManager(sheet_name, creds, headers)
    sheet_manager.ws.clear()
    sheet_manager.ws.append_row(headers)
    if rows:
        start_col = 1  # A
        end_col = len(headers)
        def col_letter(n):
            result = ''
            while n > 0:
                n, rem = divmod(n - 1, 26)
                result = chr(65 + rem) + result
            return result
        range_str = f"{col_letter(start_col)}2:{col_letter(end_col)}{len(rows)+1}"
        values = rows
        sheet_manager.ws.update(values=values, range_name=range_str)
        print(f"Uploaded {len(rows)} rows to Google Sheet '{sheet_name}'")

def main():
    args = parse_args()
    if args.output in ("google-sheets", "both") and (not args.sheet or not args.creds):
        print("--sheet and --creds are required for Google Sheets output", flush=True)
        return
    urls = read_urls(args.file)
    if not urls:
        print("No URLs found", flush=True)
        return
    HEADERS = [
        "URL", "Type", "Name", "Description", "Leader", "Start Date", "End Date", "Committee",
        "Registration Open", "Non-Priority Registration Open", "Registration Closed",
        "Mileage", "Elevation Gain", "Availability", "Capacity", "Leader's Notes",
        "Last Updated (UTC)"
    ]
    rows = collect_rows(urls, HEADERS, delay=args.delay)
    if args.output in ("csv", "both"):
        write_csv(args.output_file_name, HEADERS, rows)
    if args.output in ("google-sheets", "both"):
        upload_to_sheets(args.sheet, args.creds, HEADERS, rows)

if __name__ == "__main__":
    main()
