from urllib.parse import urlparse      #scheme | hostname | port | path | query | fragment
import tldextract                      #subdomain | domain | suffix
import os
import time
from pathlib import Path
from src.utils import ensure_dir, logging
import csv
import ipaddress

ROOT = Path(__file__).resolve().parents[3]

def read_csv(csv_path):
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as file_csv:
        reader = csv.DictReader(file_csv)
        for row in reader:
            if 'url' in row and row['url'].strip():
                rows.append({
                    'url': row['url'].strip(),
                })
    return rows

def is_valid_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def extract_url_features(url):
    parsed = urlparse(url if url.startswith(("http://", "https://")) else "https://" + url)
    scheme = parsed.scheme or ""
    domain_name = parsed.hostname or ""
    path = parsed.path or ""
    full_url = url

    ext = tldextract.extract(domain_name)
    subdomain = ext.subdomain or ""
    domain = ext.domain or ""
    suffix = ext.suffix or ""
    base_domain = f"{domain}.{suffix}" if domain and suffix else ""
    subdomain_domain = f"{subdomain}.{domain}" if subdomain and domain else ""

    f = {}

    # UF2: Count subdomain in URL
    dot_count = subdomain_domain.count('.')
    if dot_count > 2:
        f['UF2'] = 1
    elif dot_count == 2:
        f['UF2'] = 0.5
    else:
        f['UF2'] = 0

    # UF3: IP Address is domain name
    f['UF3'] = int(is_valid_ip(domain_name))

    # UF4: “@” symbol in URL
    f['UF4'] = int('@' in full_url)

    # UF5: Length of URL
    url_len = len(full_url)
    if url_len < 75:
        f['UF5'] = 0
    elif url_len < 100:
        f['UF5'] = 0.5
    else:
        f['UF5'] = 1

    # UF6: Depth of URL
    f['UF6'] = len([p for p in path.split('/') if p])

    # UF7: Redirection '//' in URL
    pos = full_url.find('//', full_url.find('//') + 2)
    f['UF7'] = int(pos > 7)

    # UF8: http/https in domain name
    f['UF8'] = int('http' in domain_name.lower() or 'https' in domain_name.lower())

    # UF9: HTTPS in scheme
    f['UF9'] = int(scheme.lower() != 'https')

    # UF10: Using URL shortening service “tinyURL”
    shortlist = ['bit.ly','bitly.com','bitly.is','j.mp','tinyurl.com','t.co','goo.gl','ow.ly','buff.ly',
                'rebrand.ly','is.gd','v.gd','soo.gd','adf.ly','shorte.st','bc.vc','linkvertise.com',
                'cutt.ly','shorturl.at','clck.ru','chilp.it','po.st','qr.ae','trib.al','lnkd.in','fb.me',
                'm.me','amzn.to','ebay.to','wp.me','youtu.be','slidesha.re','nyti.ms','bloom.bg','tiny.cc',
                'rb.gy','short.cm','s.id','u.to','ity.im','ln.is','t.ly','shrtco.de','1url.com','urlzs.com',
                'zzb.bz','x.co','q.gs','2.ly','9qr.de','zi.pe','mcaf.ee','qrco.de','qr.net','linktr.ee'
                ,'bio.link','campsite.bio']
    f['UF10'] = int(any(s in domain_name.lower() for s in shortlist))

    # UF11: Prefix or Suffix “-” in domain name
    f['UF11'] = int('-' in domain_name)

    # UF12: Existence of sensitive word
    sensitive_words = ['account', 'bank', 'login', 'signin', 'update', 'verify', 'validation', 'confirm',
                       'confirm your account', 'secure', 'security', 'access', 'restricted', 'suspended', 'alert',
                       'warning', 'urgent action required', 'payment','billing', 'password', 'reset',
                       'verification needed', 'account support', 'validate', 'activate']

    f['UF12'] = int(any(w in full_url.lower() for w in sensitive_words))

    # UF13: Existence of trendy brand name
    brands = ['microsoft','google','apple','amazon','adobe','linkedin','facebook','meta','whatsapp','spotify',
              'mastercard','booking','booking.com','paypal','dhl','telegram','onedrive','okta','sharepoint','instagram',
              'fedex','ebay']
    f['UF13'] = int(any(b in full_url.lower() for b in brands))

    # UF14: Existence of upper case letter
    f['UF14'] = int(any(c.isupper() for c in full_url))

    # UF15: Number of dots in URL
    f['UF15'] = int(full_url.count('.') > 2)

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

def main(csv_in=None, path_save_uf=None, delay=0.5):
    csv_in = csv_in or os.path.join(ROOT, "data", "raw", "phishing_urls.csv")
    path_save_uf = path_save_uf or os.path.join(ROOT, "data", "features", "phishing_url_features.csv")

    ensure_dir(os.path.dirname(path_save_uf))

    rows = read_csv(csv_in)
    logging.info(f"Loaded {len(rows)} URLs")

    extracted_urls = save_extracted_urls(path_save_uf)
    logging.info(f"Found {len(extracted_urls)} URLs already extracted")

    FIELDNAMES = ['url'] + [f'UF{i}' for i in range(2, 16)] + ['label']
    file_is_empty = (not os.path.exists(path_save_uf)) or os.path.getsize(path_save_uf) == 0

    with open(path_save_uf, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if file_is_empty:
            writer.writeheader()

        for r in rows:
            url = r['url']

            if url in extracted_urls:
                logging.info(f"Skip (already extracted): {url}")
                continue

            try:
                features = extract_url_features(url)

                row = {'url': url}
                for i in range(2, 16):
                    row[f'UF{i}'] = features.get(f'UF{i}', 0)
                row['label'] = 1

                writer.writerow(row)

                extracted_urls.add(url)
                logging.info(f"Extracted features successfully for URL: {url}")

                time.sleep(delay)
            except Exception as e:
                logging.error(f"Extraction of failure features: {url} | {e}")

    logging.info(f"Saved URL features to: {path_save_uf}")

if __name__ == "__main__":
    main()
