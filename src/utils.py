import logging
from pathlib import Path
import joblib
import os

logging.basicConfig(                    #in thông báo ra màn hình, mức thông báo là INFO trở lên
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def ensure_dir(path):                    #tạo thư mục trước khi lưu file
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def save_model(model, path):
    ensure_dir(os.path.dirname(path))
    joblib.dump(model, path)

def load_model(path):
    return joblib.load(path)


