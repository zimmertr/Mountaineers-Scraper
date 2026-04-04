def get_allowed_prefixes(filter_type):
    allowed_prefixes = set()
    if filter_type:
        types = [t.strip().lower() for t in filter_type.split(',') if t.strip()]
        if len(types) == 1:
            t = types[0]
            if t == 'trip':
                allowed_prefixes.add('https://www.mountaineers.org/activities/activities/')
            elif t in {'clinic', 'practice session', 'seminar'}:
                allowed_prefixes.add('https://www.mountaineers.org/locations-lodges/')
        else:
            # Multiple types: allow both
            allowed_prefixes = {
                'https://www.mountaineers.org/activities/activities/',
                'https://www.mountaineers.org/locations-lodges/'
            }
    else:
        # No filter_type: allow both
        allowed_prefixes = {
            'https://www.mountaineers.org/activities/activities/',
            'https://www.mountaineers.org/locations-lodges/'
        }
    return allowed_prefixes
import argparse
import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.mountaineers.org/activities/activities/@@faceted_query"

FILTER_MAP = {
    'filter_activity': 'c4',
    'filter_branch': 'c8',
    'filter_effort': 'c15',
    'filter_type': 'c16',
    'filter_climbing_category': 'c7',
    'filter_snowshoeing_category': 'c10',
    'filter_difficulty': 'c14',
}

def parse_args():
    parser = argparse.ArgumentParser(description="Collect Mountaineers activity URLs with flexible filters.")
    for arg, param in FILTER_MAP.items():
        parser.add_argument(f'--{arg.replace("_", "-")}', type=str, help=f"Comma-separated list for {param}")
    parser.add_argument('--output-filename', type=str, default='urls.txt', help='Output file name for output (default: urls.txt)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    return parser.parse_args()

def build_query(args):
    params = []
    for arg, param in FILTER_MAP.items():
        val = getattr(args, arg)
        if val:
            for v in [x.strip() for x in val.split(',') if x.strip()]:
                # Use [] for multi-value params (e.g., c4[]=Climbing)
                params.append((f"{param}[]", v))
    return params

def get_activity_links(page_html):
    soup = BeautifulSoup(page_html, 'html.parser')
    links = set()
    for a in soup.select('a.result-left'):
        href = a.get('href')
        if href:
            links.add(href)
    return links

def main():
    args = parse_args()
    params = build_query(args)
    b_start = 0
    all_links = set()

    filter_type = getattr(args, 'filter_type', None)
    allowed_prefixes = get_allowed_prefixes(filter_type)

    while True:
        query_params = [("b_start", str(b_start))] + params
        url = BASE_URL
        print(f"Fetching: {url} with params: {query_params}")
        resp = requests.get(url, params=query_params)
        if resp.status_code != 200:
            print(f"Failed to fetch {url} (status {resp.status_code})")
            break
        links = get_activity_links(resp.text)
        # Filter links by allowed prefixes
        filtered_links = set()
        for link in links:
            if any(link.startswith(prefix) for prefix in allowed_prefixes):
                filtered_links.add(link)
        if not filtered_links:
            break
        all_links.update(filtered_links)
        b_start += 20
        time.sleep(args.delay)
    output_path = args.output_filename
    with open(output_path, 'w') as f:
        for link in sorted(all_links):
            f.write(link + '\n')
    print(f"Wrote {len(all_links)} URLs to {output_path}")

if __name__ == "__main__":
    main()
