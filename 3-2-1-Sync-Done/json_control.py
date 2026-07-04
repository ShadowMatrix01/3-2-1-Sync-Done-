import json
import logging
import os
from datetime import datetime
logging.basicConfig(level=logging.WARNING, filename='manifest.log', format='%(asctime)s - %(levelname)s: %(message)s')
def json_writer(hash, path):
  list = {}
  if os.path.exists(path):
     with open(path, 'r') as f:
        try:
           list = json.load(f)
        except json.JSONDecodeError:
           logging.error("ERROR: Manifest is corrupted, rebuilding...")
     list.update(hash)
     with open(path, "w") as f:
        json.dump(list, f, indent=4)

def hash_compare(file_path, current_hash, manifest_path):
    if not os.path.exists(manifest_path):
        return "new" 
    with open(manifest_path, "r") as f:
        try:
            manifest_data = json.load(f) 
        except json.JSONDecodeError:
            return "manifest_error"
    if file_path not in manifest_data:
        return "new"
    stored_hash = manifest_data[file_path]["hash"]
    if current_hash == stored_hash:
        return "same"
    else:
        return "corrupted"

          
#https://docs.python.org/3/library/json.html for JSON exception. 
#https://www.geeksforgeeks.org/python/reading-and-writing-json-to-a-file-in-python/
