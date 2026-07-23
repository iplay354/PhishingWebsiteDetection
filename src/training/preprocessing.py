from pathlib import Path
import pandas as pd
import os

ROOT = Path(__file__).resolve().parents[2]
#=================================== hybrid features legitimate ==============================
csv_url_legitimate = pd.read_csv(os.path.join(ROOT, 'data', 'features', 'legitimate_url_features.csv'))
csv_hyperlink_legitimate = pd.read_csv(os.path.join(ROOT, 'data', 'features', 'legitimate_hyperlink_features.csv'))

csv_url_legitimate = csv_url_legitimate.drop(columns=['label'], errors='ignore')

merged = pd.merge(csv_url_legitimate, csv_hyperlink_legitimate, on='url', how='inner')
merged.to_csv(os.path.join(ROOT, 'data', 'features', 'hybrid_features_legitimate.csv'), index=False)


#==================================== hybrid features phishing ================================
csv_url_phishing = pd.read_csv(os.path.join(ROOT, 'data', 'features', 'phishing_url_features.csv'))
csv_hyperlink_phishing = pd.read_csv(os.path.join(ROOT, 'data', 'features', 'phishing_hyperlink_features.csv'))

csv_url_phishing = csv_url_phishing.drop(columns=['label'], errors='ignore')

merged = pd.merge(csv_url_phishing, csv_hyperlink_phishing, on='url', how='inner')
merged.to_csv(os.path.join(ROOT, 'data', 'features', 'hybrid_features_phishing.csv'), index=False)


#===================================== hybrid features legitimate + phishing =========================================
file1 = pd.read_csv(os.path.join(ROOT, 'data', 'features', 'hybrid_features_legitimate.csv'))
file2 = pd.read_csv(os.path.join(ROOT, 'data', 'features', 'hybrid_features_phishing.csv'))

file = pd.concat([file1, file2], ignore_index=True)

file.to_csv(os.path.join(ROOT, 'data', 'features', 'hybrid_features.csv'), index=False)

#===================================== hybrid features delete "URL" train =====================================

f = pd.read_csv(os.path.join(ROOT, 'data', 'features', 'hybrid_features.csv'))

f = f.drop(columns=['url'], errors='ignore')

f.to_csv(os.path.join(ROOT, 'data', 'features_full', 'hybrid_features_full.csv'), index=False)


