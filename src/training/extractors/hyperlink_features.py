from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin    #scheme | hostname | port | path | query | fragment
from collections import Counter
from pathlib import Path
from src.utils import ensure_dir, logging
import tldextract
import time
import os
import csv

ROOT = Path(__file__).resolve().parents[3]

def read_html_and_url(filepath):
    url = None
    html_content = ""

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) >= 2 and lines[0].strip().startswith("<!-- url:"):
        url_line = lines[0].strip()
        url = url_line[len("<!-- url:"):].strip().rstrip('\n').strip()
        html_content = "".join(lines[2:])
    else:
        html_content = "".join(lines)

    return url, html_content

def is_external(href, base_domain):
    try:
        h = urlparse(href)
        hostname = h.hostname
        ext = tldextract.extract(hostname)
        domain = ext.domain or ""
        suffix = ext.suffix or ""
        href_base_domain = f"{domain}.{suffix}" if domain and suffix else ""
        return href_base_domain != base_domain
    except Exception:
        return True

def extract_hyperlink_features(html_text, url):
    soup = BeautifulSoup(html_text, "lxml")
    parsed = urlparse(url if url.startswith(("http","https")) else "http://"+url)
    domain_name = parsed.hostname

    ext = tldextract.extract(domain_name)
    domain = ext.domain or ""
    suffix = ext.suffix or ""
    base_domain = f"{domain}.{suffix}" if domain and suffix else ""

    anchors = soup.find_all('a')
    forms = soup.find_all('form')
    links = soup.find_all('link')

    total_anchors = len(anchors)

    out_anchors = 0
    null_anchors = 0

    href_list = []

    for a in anchors:
        href = (a.get('href') or "").strip()
        if href in ["", "#", "#content"] or href.lower().startswith("javascript"):
            null_anchors += 1
        if href:
            full_href = urljoin(url, href)
            href_list.append(full_href)
            if is_external(full_href, base_domain):
                out_anchors += 1

    f = {}

    # HF1: No hyperlink
    total_hyperlink = total_anchors
    f['HF1'] = int(total_hyperlink == 0)

    # HF2: Internal hyperlink ratio
    in_anchors = total_anchors - out_anchors - null_anchors
    internal_ratio = in_anchors / total_anchors if total_anchors > 0 else 0
    f['HF2'] = 0 if internal_ratio >= 0.5 else 1

    # HF3: External hyperlink ratio
    external_ratio = out_anchors / total_anchors if total_anchors > 0 else 0
    f['HF3'] = 1 if external_ratio > 0.5 else 0

    # HF4: Internal/ External CSS
    f['HF4'] = int(any(
        l.get('rel') and 'stylesheet' in l.get('rel') and
        l.get('href') and is_external(urljoin(url, l.get('href')), base_domain)
        for l in links
    ))

    # HF5: Form action
    f['HF5'] = 0
    for form in forms:
        action = (form.get('action') or "").strip().lower()
        if action in ["", "#", "javascript:void(0)"]:
            f['HF5'] = 1
            break
        if action.endswith(".php"):
            f['HF5'] = 1
            break
        if is_external(urljoin(url, action), base_domain):
            f['HF5'] = 1
            break

    # HF6: Null hyperlink
    null_ratio = null_anchors / total_anchors if total_anchors > 0 else 0
    f['HF6'] = 1 if null_ratio > 0.34 else 0

    # HF7: External favicon
    f['HF7'] = 0
    for l in links:
        rel = " ".join(l.get('rel', []))
        if 'icon' in rel.lower():
            href = l.get('href') or ""
            if href and is_external(urljoin(url, href), base_domain):
                f['HF7'] = 1
                break

    # HF8: Common page ratio
    f['HF8'] = 0
    if total_anchors > 0 and href_list:
        most_common = Counter(href_list).most_common(1)[0][1]  # đếm và trả lớn nhất
        f['HF8'] = most_common / total_anchors

    # HF9: Common page in footer
    footer = soup.find('footer')
    f['HF9'] = 0
    if footer:
        footer_links = [urljoin(url, a.get('href'))
                        for a in footer.find_all('a') if a.get('href')]
        if footer_links:
            most_common_footer = Counter(footer_links).most_common(1)[0][1]
            f['HF9'] = most_common_footer / len(footer_links)

    # HF10: SFH
    f['HF10'] = 0
    for form in forms:
        action = (form.get('action') or "").strip().lower()
        if action in ["", "about:blank"]:
            f['HF10'] = 1
            break
        if is_external(urljoin(url, action), base_domain):
            f['HF10'] = max(f['HF10'], 0.5)

    return f

def save_extracted_urls(path):
    extracted = set()
    if not os.path.exists(path):
        return extracted
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('url')
            if url and url.strip():
                extracted.add(url.strip())
    return extracted

def main(folder_save_html=None, path_save_hf=None, delay=0.5):
    folder_save_html = folder_save_html or os.path.join(ROOT, "data", "crawled_html", "phishing")
    path_save_hf = path_save_hf or os.path.join(ROOT, "data", "features", "phishing_hyperlink_features.csv")

    ensure_dir(os.path.dirname(path_save_hf))

    files = [f for f in os.listdir(folder_save_html) if f.endswith(".html")]

    extracted_urls = save_extracted_urls(path_save_hf)
    logging.info(f"Found {len(extracted_urls)} URLs already extracted")

    FIELDNAMES = ['url'] + [f'HF{i}' for i in range(1, 11)] + ['label']
    file_is_empty = (not os.path.exists(path_save_hf)) or os.path.getsize(path_save_hf) == 0

    with open(path_save_hf, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        if file_is_empty:
            writer.writeheader()

        for f in files:
            filepath = os.path.join(folder_save_html, f)
            url, html = read_html_and_url(filepath)

            if url in extracted_urls or not url or not html.strip():
                logging.info(f"Skip (already extracted): {url}")
                continue

            try:
                features = extract_hyperlink_features(html, url)

                row = {'url': url,}
                for i in range(1, 11):
                    row[f'HF{i}'] = features.get(f'HF{i}', 0)
                row['label'] = 1

                writer.writerow(row)

                extracted_urls.add(url)
                logging.info(f"Successfully extracted HTML features of URL: {url}")

                time.sleep(delay)
            except Exception as e:
                logging.error(f"Failed to extract HTML features of URL: {url} | {e}")

    logging.info(f"Saved HTML features to: {path_save_hf}")


if __name__ == '__main__':
    main()
