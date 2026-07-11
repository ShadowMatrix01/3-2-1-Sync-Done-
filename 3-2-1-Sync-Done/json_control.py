import json
import logging
import os
from datetime import datetime
val = 0
logging.basicConfig(level=logging.INFO, filename='loginfo.log', format='%(asctime)s - %(levelname)s: %(message)s',force=True)
def json_writer(hash, path):
  global val
  val = val + len(hash)
  list = {}
  if os.path.exists(path): #It was treating an empty manifest as corrupt, when not..
     with open(path, 'r') as f:
        try:
           list = json.load(f)
        except json.JSONDecodeError:
           logging.error(f"Manifest is corrupted, rebuilding. Date and time: {datetime.now().isoformat()}")
     list.update(hash)
     with open(path, "w") as f:
        json.dump(list, f, indent=4)
     logging.info(f"Successfully updated manifest with {len(hash)} entries.")
def hash_compare(file_path, current_hash, manifest_path):
    if not os.path.exists(manifest_path):
        return "new" 
    if os.path.getsize(manifest_path) == 0:
        return "new"
    with open(manifest_path, "r") as f:
        try:
            manifest_data = json.load(f) 
        except json.JSONDecodeError:
            return "new"
    if file_path not in manifest_data:
        return "new"
    stored_hash = manifest_data[file_path]["hash"]
    if current_hash == stored_hash:
        return "same"
    else:
        return "corrupted"

          
#https://docs.python.org/3/library/json.html for JSON exception. 
#https://www.geeksforgeeks.org/python/reading-and-writing-json-to-a-file-in-python/
