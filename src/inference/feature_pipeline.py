import numpy as np
import requests

from src.training.extractors.url_features import extract_url_features
from src.training.extractors.hyperlink_features import extract_hyperlink_features

def build_feature_vector(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        html = r.text
        if not html.strip():
            html = None
    except Exception:
        html = None

    url_features = extract_url_features(url)

    if html:
        hyperlink_features = extract_hyperlink_features(html, url)
    else:
        hyperlink_features = {
            key: 0 for key in extract_hyperlink_features("", url).keys()
        }

    features = (list(url_features.values()) +list(hyperlink_features.values()))

    return np.array(features).reshape(1, -1)
