import json
import logging
import os
from datetime import datetime
val = 0
logging.basicConfig(level=logging.INFO, filename='loginfo.log', format='%(asctime)s - %(levelname)s: %(message)s',force=True)
def load_manifest(path): #Rewritten, because my old program was opening the manifest everytime so now it is O(n) instead of O(n^2).
     if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
     with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logging.error(f"{path} is corrupted, rebuilding. Date and time: {datetime.now().isoformat()}")
            return {}
def json_writer(hash_json, path):
  global val
  val = val + len(hash_json)
  arr = {}
  if os.path.exists(path): #It was treating an empty manifest as corrupt, when it wasn't.
     with open(path, 'r') as f:
        try:
           arr = json.load(f)
        except json.JSONDecodeError:
           logging.error(f"{path} is corrupted, rebuilding. Date and time: {datetime.now().isoformat()}")
     arr.update(hash_json)
     with open(path, "w") as f:
        json.dump(arr, f, indent=4)
  else:
    print(f"{path} does not exist, creating {path} and exiting program.")
    logging.error(f"{path} does not exist, creating {path}! and exiting program")
    with open(path, "w") as f:
         json.dump({}, f)
    exit()
def hash_compare(file_path, current_hash, manifest_data):
    if file_path not in manifest_data:
        return "new"
    stored_hash = manifest_data[file_path]["hash"]
    if current_hash == stored_hash:
        return "same"
    else:
        return "corrupted"

          
#https://docs.python.org/3/library/json.html for JSON exception. 
#https://www.geeksforgeeks.org/python/reading-and-writing-json-to-a-file-in-python/
