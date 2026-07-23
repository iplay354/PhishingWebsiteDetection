from pathlib import Path
from src.utils import ensure_dir, logging
import csv
import requests
import os
import time

ROOT = Path(__file__).resolve().parents[3] #phishing project

def read_csv(csv_path):            #csv_path: file csv                       # chuẩn hoá về dạng {"id": ..., "url": ...}
    rows = []
    count = 1
    with open(csv_path, newline='', encoding='utf-8') as file_csv:
        reader = csv.DictReader(file_csv)
        for row in reader:
            if 'id' in row and 'url' in row and row['id'].strip() and row['url'].strip():
                rows.append({
                    'id': row['id'].strip(),
                    'url': row['url'].strip(),
                })
            else:
                rows.append({
                    'id' : f"html_{count}",
                    'url': row['url'].strip(),
                })
            count += 1
    return rows

def fetch_html(url, outpath_crawl, timeout=15):    #outpath: nơi lưu file html, timeout: thời gian chờ yêu cầu     #tải html từ url
    headers = {
        "User-Agent": "phish-detect-bot/1.0 (+https://example.org)"
    }

    try:
        r = requests.get(url, headers = headers, timeout = timeout, allow_redirects=True)
        content = r.text
        status = r.status_code
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")
        return

    if content.count('\n') <= 2:
        logging.warning(f"Content too short or empty for URL {url}, not saving file.")
        if os.path.exists(outpath_crawl):
            os.remove(outpath_crawl)
        return

    ensure_dir(os.path.dirname(outpath_crawl))   # os.path.dirname: trả về thư mục cha, vidu: html/css/php -> html/css

    with open(outpath_crawl, "w", encoding="utf-8") as f:
        f.write(f"<!-- url: {url}\nstatus: {status} -->\n")
        f.write(content)

def main(csv_in=None, path_save_html=None, delay=0.5):                                                  #hàm chính
    csv_in = csv_in or os.path.join(ROOT, "data", "raw", "phishing_urls.csv")
    path_save_html = path_save_html or os.path.join(ROOT, "data", "crawled_html", "phishing")

    ensure_dir(path_save_html)

    rows = read_csv(csv_in)
    logging.info(f"Loaded {len(rows)} rows from {csv_in}")

    for r in rows:
        uid = r['id']
        url = r['url']

        outpath_crawl = os.path.join(path_save_html, f"{uid}.html")

        if os.path.exists(outpath_crawl):
            logging.info(f"Exists {outpath_crawl}, skipping")
            continue

        logging.info(f"Fetching {url} -> {outpath_crawl}")
        fetch_html(url, outpath_crawl)

        time.sleep(delay)

if __name__ == "__main__":
    main()