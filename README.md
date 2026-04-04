# Mountaineers Activity Scraper

> ⚠️ **Please use this responsibly and DO NOT abuse their servers with aggressive scraping!** ⚠️

## Summary

Mountaineers Activity Scraper can be used to collect and parse activity data from [Mountaineers.org](https://www.mountaineers.org/activities/activities). Use it to gather URLs for climbing and outdoor activities and then extract the data to a CSV file or Google Sheets for analysis and planning.

![Example Screenshot](screenshot.png)

## Requirements
- Docker
- (Optional) Google Cloud account & service account JSON for Sheets export

## Instructions

### 1. Collect Activity URLs

```bash
# Collect all `Climbing` activites hosted by the `Seattle` branch. 
# See Collection Filters below for configuration
docker run --rm \
    -v $(pwd):/data \
    $(docker build -q .) \
    --mode collect \
    --filter-branch Seattle \
    --filter-activity Climbing \
    --output /data/urls_seattle_climbing.txt
```

### 2. Scrape Activity Data to CSV

```bash
docker run --rm \
    -v $(pwd):/data \
    $(docker build -q .) \
    --mode scrape \
    --file /data/urls_seattle_climbing.txt \
    --output csv \
    --output-file-name /data/output.csv
```

### 3. Scrape Activity Data to Google Sheets

```bash
# See Google Sheets Setup section below before use
docker run --rm \
    -v $(pwd):/data \
    $(docker build -q .) \
    --mode scrape \
    --file /data/urls_seattle_climbing.txt \
    --output google-sheets \
    --sheet "Mountaineers Trips" \
    --creds /data/google_cloud_credentials.json
```

## Arguments

| Argument              | Required? | Description                                                                                 |
|-----------------------|-----------|---------------------------------------------------------------------------------------------|
| --mode                | Yes       | `collect` to gather a list of URLs, `scrape` to parse activity data from a list of URLs                                   |
| --output              | Yes*      | In `collect` mode: output file path for URLs. In `scrape` mode: output format (`csv`, `google-sheets`, or `both`) |
| --file                | Yes*      | A file containing a list of URLs to scrape (required for `scrape` mode)                                 |
| --output-file-name    | No        | Output CSV file name (default: `output.csv`)                                                |                                                    |
| --sheet               | Yes*      | Google Sheet name (required if `--output google-sheets`)                                    |
| --creds               | Yes*      | Path to a JSON file containing Google Cloud Service Account credentials (required if `--output google-sheets`)             |
| --delay               | No        | Delay between requests in seconds (default: 1 second)                                            |

## Collection Filters
The following filters are available for use with `--mode collect`:

| Website Filter Option         | CLI Flag             | Example Value(s)         |
|---------------------|----------------------|--------------------------|
| "I want to go..."            | --filter-activity    | Climbing, Hiking         |
| "With this branch..."              | --filter-branch      | Seattle, Tacoma          |
| "I'd like it to be..."              | --filter-effort      | Moderate, Casual         |
| "Type..."                | --filter-type        | Trip, Clinic             |
| "Climbing Categories"   | --filter-climbing-category | "Basic Alpine", "Rock Climb" |
| "Snowshoeing Categories" | --filter-snowshoeing-category | Basic, Intermediate |
| "Difficulties""          | --filter-difficulty  | Easy, "Bikepacking Gravel I", T3, "Winter Scramble"           |

You can combine filters for refined results. For example:

```bash
docker run --rm \
    -v $(pwd):/data \
    $(docker build -q .) \
    --mode collect \
    --filter-activity Climbing,Scrambling \
    --filter-branch Seattle,Foothills \
    --filter-type Trip \
    --output /data/urls.txt
```

## Google Sheets Setup

To export activity data directly to Google Sheets, follow these steps:

1. **Create a Google Cloud Project**
    - Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project.

2. **Enable Required APIs**
    - Enable both the [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) and the [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) for your project.

3. **Create a Service Account**
    - In the [Service Accounts section](https://console.cloud.google.com/iam-admin/serviceaccounts), create a new service account.

4. **Generate and Download Credentials**
    - Add a new key to your service account (choose JSON format).
    - Download the credentials file and save it as `google_cloud_credentials.json` in your project directory.

5. **Create a Google Sheet**
    - Make a new spreadsheet in [Google Sheets](https://sheets.google.com/).

6. **Share the Sheet with Your Service Account**
    - Open your `google_cloud_credentials.json` and copy the `client_email` value.
    - Share your Google Sheet with this email address (as an editor).

You're now ready to use the `--output google-sheets` option!

## Useful Conditional Formatting Rules for Google Sheets:

1. Mark all FULL activities as red:
    ```
    Apply to Range: A2:Z995
    Format rules if: Custom formula is
    =ISNUMBER(SEARCH("FULL",$N2))
    ```

2. Mark all open registration activities as blue
    ```
    Apply to Range: A2:Z995
    Format rules if: Custom formula is
    =DATEVALUE(LEFT($I2,10)) <= TODAY()
    ```

3. Mark all Foothills activities as green
    ```
    Apply to Range: A2:Z995
    Format rules if: Custom formula is
    =ISNUMBER(SEARCH("Foothills",$H2))
    ```
