import json
import logging
from filelock import FileLock

DATA_FILE = "data/labels.json"
LOCK_FILE = DATA_FILE + ".lock"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("filelock").setLevel(logging.WARNING)  # Suppress filelock debug messages

def read_labels():
    with FileLock(LOCK_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # logging.info("Labels read successfully.")
                return data
        except Exception as e:
            logging.error("Failed to read labels: %s", e)
            return {}

def write_labels(data):
    with FileLock(LOCK_FILE):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                logging.info("Labels written successfully.")
        except Exception as e:
            logging.error("Failed to write labels: %s", e)

def filter_sentences_by_property(property_name):
    data = read_labels()
    if property_name in data:
        return data[property_name].get("texts", [])
    return []

def get_next_unlabeled_sentence(property_name, annotations):
    sentences = filter_sentences_by_property(property_name)
    for sentence in sentences:
        if sentence not in annotations or not annotations[sentence]:
            return sentence
    return None
