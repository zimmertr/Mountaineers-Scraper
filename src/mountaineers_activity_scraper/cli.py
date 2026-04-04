import sys
import argparse
from mountaineers_activity_scraper import collect_urls, scraper

def main():
    parser = argparse.ArgumentParser(description="Unified CLI for Mountaineers Activity Scraper")
    parser.add_argument('--mode', choices=['collect', 'scrape'], required=True, help='Mode: collect (URLs) or scrape (details)')
    args, rest = parser.parse_known_args()

    if args.mode == 'collect':
        sys.argv = [sys.argv[0]] + rest
        collect_urls.main()
    elif args.mode == 'scrape':
        sys.argv = [sys.argv[0]] + rest
        scraper.main()
    else:
        parser.error('Unknown mode')

if __name__ == "__main__":
    main()
