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
def json_writer(hash, path):
  global val
  val = val + len(hash)
  list = {}
  if os.path.exists(path): #It was treating an empty manifest as corrupt, when not..
     with open(path, 'r') as f:
        try:
           list = json.load(f)
        except json.JSONDecodeError:
           logging.error(f"{path} is corrupted, rebuilding. Date and time: {datetime.now().isoformat()}")
     list.update(hash)
     with open(path, "w") as f:
        json.dump(list, f, indent=4)
     logging.info(f"Successfully updated {path} with {len(hash)} entries.")
  else:
    print(f"{path} does not exist, please create file manually!")
    logging.error(f"{path} does not exist, please create file manually!")
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
