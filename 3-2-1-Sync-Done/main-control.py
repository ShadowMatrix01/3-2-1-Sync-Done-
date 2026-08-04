#!/usr/bin/env python3 
import argparse #Needed for cmd to ensure user is given choice
#between full and partial backup.
import os
from dotenv import load_dotenv
import ijson #Because otherwise, retrieving the file from manifest would be too inefficient.
import logging
import hashlib
from azure.storage.blob import BlobClient, ContainerClient, BlobServiceClient
from azure.core.exceptions import HttpResponseError
from datetime import datetime
from hashHOT import hash256_caller
from json_control import json_writer, hash_compare, load_manifest
from tqdm import tqdm
from VT_online_check import online_check
from notify import main_menu, local_notification_check, webhook_check, VT_check, alert_preferences
from plyer import notification
load_dotenv()
BATCH_SIZE = 4096 #Constant, because the amount of IO operations was slowing down the project by a lot.
buffer_arr = {}
seen_and_banned = {}
write_now = False
vt_check = False
local_notif = False
webhook_notif = False
EXCLUDED = ["manifest.json", "loginfo.log", "manifest2.json", "manifest3.json", "cloudlog.log", "VT_check.log", "VT_online_check.py"]
def download_blob():
    global buffer_arr
    buffer_arr = {}
    azure_connection_string = os.getenv("AZURE_CONNECT_STR")
    azure_container_name = os.getenv("AZURE_CONTAINER")
    if azure_connection_string is None:
       print("Error: AZURE_CONNECT_STR not found. Please create a .env file based on .env.example")
       return
    if not azure_container_name:
       print("Error: AZURE_CONTAINER not found. Please create a .env file based on .env.example")
       return
    try:
         blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
         container_client = blob_service_client.get_container_client(container=azure_container_name)
         blob_list = container_client.list_blobs()
         for blob in blob_list:
            blob_name = blob.name
            modified = blob.last_modified
            file_size = blob.size
            sha256 = hashlib.sha256()  
            try:
                  blob_client = container_client.get_blob_client(blob_name)
                  stream_data = blob_client.download_blob()
                  with tqdm(total=stream_data.size, desc="Hashing file(s) from the cloud", colour="yellow", unit="B",  unit_scale=True, unit_divisor=1024) as pbar:
                        for chunk in stream_data.chunks():
                           sha256.update(chunk)
                           pbar.update(len(chunk))
                  file_hash = sha256.hexdigest()
                  if (blob_name and file_hash) and blob_name not in EXCLUDED:
                           buffer_arr[blob_name] = {
                                       "hash": file_hash,
                                       "last_seen": datetime.now().isoformat(),
                                       "mtime": round(modified.timestamp(), 4) if modified else None, #Was giving me typerrors of JSON, so wrapped
                                       "size": file_size
                           }
                  if ((len(buffer_arr) % BATCH_SIZE == 0) or write_now) and buffer_arr: #Prevents edge case that was happening during testing.
                        json_writer(buffer_arr, "manifest3.json")
                        buffer_arr = {} 
            except HttpResponseError as e:
                print(f"Azure HTTP Error {e.status_code} on file {blob_name}: {e.message}")
                logging.error(f"Azure HTTP Error {e.status_code} on {blob_name}: {e}")                  
                #https://pypi.org/project/azure-storage-blob/
                #https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-list-python
                #https://learn.microsoft.com/en-us/python/api/azure-core/azure.core.exceptions?view=azure-python
                #https://learn.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob.storagestreamdownloader?view=azure-python#azure-storage-blob-storagestreamdownloader-download-to-stream
    except HttpResponseError as e:
        print(f"Azure Container Error: {e.status_code}: {e.message}")
        logging.error(f"Azure Container Error: {e.status_code}: {e}")
    except Exception as e:
        print(f"Unexpected Azure Error: {e}")
        logging.error(f"Unexpected Azure Error: {e}")
    if buffer_arr:
       json_writer(buffer_arr, "manifest3.json")
def validate(): #Because otherwise, invalid json would be accepted, so it is checked before anything.
    setup = alert_preferences("main-control")
    if not setup:
       print("\n\nPlease check .env file, and run mode C for setup validation.")
       exit()
    global local_notif
    global webhook_notif
    global vt_check
    global azure_cloud_hash
    vt_check = VT_check("main-control")
    local_notif = local_notification_check("main-control")
    webhook_notif = webhook_check("main-control")
    #For now, this is left empty, but I will add way to verify cloud is working.
def argCV():
    #Command Line Interface CLI, similar to C which makes sense.
    #considering python is an interpreted language.
    arg = argparse.ArgumentParser(description="3-2-1 Sync Done! A Data Integrity Solution")
    arg.add_argument("--source", required=True, help="REQUIRED: Please add root directory as a string (e.g. \"C:\\Users\\Username\").")
    arg.add_argument("--source2", required=False, help="Optional: Add second directory to compare as a string (e.g. \"C:\\Users\\Username\")")
    arg.add_argument("--ext", help="Optional: Only backup files by extension (as a \"string\") (e.g., \".jpg\", \".pdf\", etc.)")
    arg.add_argument("--mode", required=True, 
                     help="REQUIRED: Mode A: Hash Files.\nMode 1B: Check FILE integrity "
                     "in manifest.json.\nMode 2B: Check FILE integrity in manifest2.json" 
                     "\nMode 3B: Check if Notifications, Webhook, and VT API are working (use a random string for --source)")
    return arg.parse_args()
def retrieve_file(target_path, manifest_data):
    if not os.path.exists(manifest_data) or os.path.getsize(manifest_data) == 0:
        print(f"Error: The manifest file '{manifest_data}' is empty or does not exist. Please create it manually.")
        return None
    path = os.path.abspath(target_path)
    try:
      with open(manifest_data, 'rb') as f:
            for file_path, info in ijson.kvitems(f, ''):
               if file_path == path:
                  return info
    except ijson.common.IncompleteJSONError:
        print(f"Error: The manifest '{manifest_data}' contains invalid or incomplete JSON. Please check the manifest manually.")
        logging.error(f"{manifest_data} is invalid or incomplete JSON.Please check the manifest manually.")
        return None
    return None
    #https://pypi.org/project/ijson/
def check_if_file_exists(file_path, manifest_data):
    check = retrieve_file(file_path, manifest_data)
    if not check:
       print(f"Sorry, but {file_path} was not found in {manifest_data}")
       return
    if not os.path.exists(file_path):
       print(f"ALERT! {file_path} was not found on the disk.")
       print(f"\nLast known hash: {check['hash']}\nLast seen: {check['last_seen']}\nLast known modified time: {check['mtime']}\nLast known size: {check['size']} bytes.")
       logging.critical(f"ALERT! {file_path} was not found on the disk.\nLast known hash: {check['hash']}\nLast seen: {check['last_seen']}\nLast known modified time: {check['mtime']}\nLast known size: {check['size']} bytes.")
       return
    hash = hash256_caller(file_path)
    if hash == check['hash']:
       print(f"The file {file_path} was successfully verified. No changes have been detected from the manifest.") 
    else:
       print(f"ALERT! {file_path} has been modified or corrupted since it was last seen!")
       logging.warning(f"{file_path} has been modified or corrupted since it was last seen.")
def total_files(directory, extension):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if extension is not None and not file.endswith(extension):
                continue
            if file in EXCLUDED:
                continue
            count += 1
    return count
def source_updater(root, files, pbar, manifest_data, this_one):
    global seen_and_banned
    for file in files:
        if argv.ext and not file.endswith(argv.ext):
           continue
        if os.path.basename(file) in EXCLUDED:
           continue
        if file in seen_and_banned:
           continue
        file_path = os.path.normpath(os.path.join(root, file))
        try:
            f_stat = os.stat(file_path)
            cur_mtime = round(f_stat.st_mtime, 4) #Avoids inconsentencies in floating point times.
            cur_size = f_stat.st_size
        except OSError:
            continue
        if file_path in manifest_data:
           data = manifest_data[file_path]
           if data.get("mtime") == cur_mtime and data.get("size") == cur_size:
              pbar.update(1)
              continue
        hash_calc = hash256_caller(file_path)
        if hash_calc:
           status = hash_compare(file_path, hash_calc, manifest_data)
           if "new" in status: 
                manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
           elif "corrupted" in status:
                 if local_notif:
                    try:
                      notification.notify(
                           title="Corrupted File Warning!",
                           message=f"{file} has been changed or is corrupted, please select an option in the program!",
                           app_name="3-2-1-Sync-Done!",
                           timeout=5
                      )
                    except Exception:
                           pass           
                 pbar.write(f"\n\nWARNING! This file {file} has been changed or corrupted!")
                 while True:
                     sel = input("Type 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ").strip().upper()
                     if sel == "CON":
                        manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
                        pbar.write("\n\nManifest has been updated, continuing program operation.")
                        break
                     elif sel == "CONVT" and vt_check:
                        pbar.write("\n\nPlease wait while the program checks the global virus database...")
                        online_check(hash_calc, file_path, pbar, local_notif, webhook_notif)
                        break
                     elif sel == "EXIT":
                        pbar.write("\n\nProgram quitting for data integrity purposes. Please check manifest.json and loginfo.log")
                        exit()
                     else:
                        if sel == "CONVT" and not vt_check:
                           pbar.write("\n\nPlease enable VT check in .env, and please run mode C for setup validation.")
                        else:
                           pbar.write("\n\nInvalid input. Please try again.")
                        continue
           elif "same" in status:
                manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
        else:
          pbar.write(f"FAILURE: The following file {file} could not be hashed. Check loginfo.log for information.")  
          seen_and_banned[file_path] = None
        pbar.update(1)
def manifest_updater(file_path, hash_calc, write_now, which_one):
    global buffer_arr #Global because buffer_arr needs to be accessed globally.
    if (file_path and hash_calc) and os.path.basename(file_path) not in EXCLUDED:
         stat = os.stat(file_path) #Just like C, with stat.
         buffer_arr[file_path] = {
                     "hash": hash_calc,
                     "last_seen": datetime.now().isoformat(),
                     "mtime": round(stat.st_mtime, 4), 
                     "size": stat.st_size
         }
    if ((len(buffer_arr) % BATCH_SIZE == 0) or write_now) and buffer_arr: #Prevents edge case that was happening during testing.
        if which_one == "source":
           json_writer(buffer_arr,"manifest.json")
        else:
           json_writer(buffer_arr,"manifest2.json")
        buffer_arr = {}  
argv = argCV()
if argv.source == " " and not (argv.mode == "C" or argv.mode =="D"):
   print("ERROR: An empty string " " was provided. This is only allowed for mode C and mode D.")
   exit()
log_file = "cloudlog.log" if argv.mode == "D" else "loginfo.log" #I have to rework
#the log in json_control, to avoid it being written to the main log, and also condense it since the log is way too big for
#this
logging.basicConfig(level=logging.WARNING, filename=log_file, format='%(asctime)s - %(levelname)s: %(message)s')
if argv.mode == "A":
   validate()
   print("Please wait while the program discovers the total number of files in the directory(s)...")
   total = total_files(argv.source, argv.ext)
   manifest_source = load_manifest("manifest.json")
   with tqdm(total=total, desc="Hashing files, please wait", colour="green") as pbar:
         for root, dirs, files in os.walk(argv.source):
            source_updater(root, files, pbar, manifest_data=manifest_source, this_one="source")
   manifest_updater(None, None, write_now=True, which_one="source")
   if argv.source2: #Because it would crash, for obvious reasons.
      buffer_arr = {}
      manifest_target = load_manifest("manifest2.json")
      total = total_files(argv.source2, argv.ext)
      with tqdm(total=total, desc="Hashing second batch of files, please wait", colour="blue") as pbar:
         for root, dirs, files in os.walk(argv.source2):
            source_updater(root, files, pbar, manifest_data=manifest_target, this_one="target")
      manifest_updater(None, None, write_now=True, which_one="target")
elif (argv.mode == "1B" or argv.mode == "2B") and not argv.source2:
     validate()
     if argv.mode == "1B":
        manifest = "manifest.json"
     else:
        manifest = "manifest2.json"
     check_if_file_exists(argv.source, manifest)
elif argv.mode == "C":
     main_menu("notify")
elif argv.mode == "D":
     #validate()
     download_blob()
else:
    if not argv.source2:
       print(f"{argv.mode} is not a valid mode. Please try again.")
    else:
       print(f"Please only use --source and not --source2. Thank you!")
#os.walk(): https://www.w3schools.com/python/ref_os_walk.asp
#shebang: https://realpython.com/python-shebang/ 
#Progress barhttps://tqdm.github.io/