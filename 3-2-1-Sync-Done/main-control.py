#!/usr/bin/env python3 
import argparse #Needed for cmd to ensure user is given choice
#between full and partial backup.
import os
from dotenv import load_dotenv
import ijson #Because otherwise, retrieving the file from manifest would be too inefficient.
import logging
import hashlib
import json
import time
import schedule
import functools
from pytz import timezone
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
from datetime import datetime
from hashHOT import hash256_caller
from json_control import json_writer, hash_compare, load_manifest
from tqdm import tqdm
from VT_online_check import online_check
from notify import main_menu, local_notification_check, webhook_check, VT_check, alert_preferences, alert_sound, schedule_preferences
from plyer import notification
from pytz import timezone
load_dotenv()
BATCH_SIZE = 4096 #Constant, because the amount of IO operations was slowing down the project by a lot.
buffer_arr = {}
write_now = False
vt_check = False
local_notif = False
webhook_notif = False
EXCLUDED = ["manifest.json", "manifest2.json", "manifest_cloud.json", "manifest.log", "manifest2.log", "manifest_cloud.log", "VT_check.log", "VT_online_check.py"]     
def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                print(traceback.format_exc())
                logging.critical(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator
#I could not use standard exceptions, so decorator and wrapper taken from docs for scheduler.
#https://schedule.readthedocs.io/en/stable/exception-handling.html
@catch_exceptions(cancel_on_failure=True)
def download_blob(extension, manifest_data, pref):
    global buffer_arr
    buffer_arr = {}
    azure_connection_string = os.getenv("AZURE_CONNECT_STR")
    azure_container_name = os.getenv("AZURE_CONTAINER")
    if not azure_connection_string :
       print("Error: AZURE_CONNECT_STR not found. Please create a .env file based on .env example")
       return
    if not azure_container_name:
       print("Error: AZURE_CONTAINER not found. Please create a .env file based on .env example")
       return
    try:
         blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
         container_client = blob_service_client.get_container_client(container=azure_container_name)
         blob_list = container_client.list_blobs()
         for blob in blob_list:
            move_on = False
            blob_name = blob.name
            modified = blob.last_modified
            cur_mtime = round(modified.timestamp(), 4) if modified else None
            file_size = blob.size
            sha256 = hashlib.sha256() 
            if blob_name in EXCLUDED:
               continue 
            if extension is not None and not blob_name.endswith(extension):
               continue
            try:
                  if blob_name in manifest_data:
                     with tqdm(total=file_size, desc=f"Verifying blob {blob_name} from cloud vs local", colour="magenta", unit="B",  unit_scale=True, unit_divisor=1024) as pbar:                    
                              data = manifest_data[blob_name]
                              mtime = data.get("mtime")
                              if mtime == cur_mtime and data.get("size") == file_size:
                                 blob_hash = data.get("hash")
                                 manifest_updater_cloud(blob_name, blob_hash, cur_mtime, file_size, write_now=False)
                                 pbar.update(file_size)
                                 continue
                              else:
                                 if local_notif:
                                    try:
                                       alert_sound()
                                       notification.notify(
                                             title="Corrupted File Warning!",
                                             message=f"{blob_name} has been changed or is corrupted, please select an option in the program!",
                                             app_name="3-2-1-Sync-Done!",
                                             timeout=5
                                       )
                                    except Exception:
                                       pass
                                 pbar.clear()
                                 pbar.write(f"WARNING! The blob {blob_name} has been changed or corrupted!")
                                 pbar.refresh() 
                                 while True:
                                       if pref is None:
                                          pbar.write("Type 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ")
                                          pbar.refresh() 
                                          sel = input(" ").strip().upper()
                                       else:
                                          if pref == "manual":
                                             pbar.write("Type 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ")
                                             pbar.refresh() 
                                             sel = input(" ").strip().upper()
                                          elif pref == "false":
                                             sel = "CON"
                                          elif pref == "true":
                                             sel = "CONVT"
                                          else:
                                             pbar.write("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                                             logging.warning("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                                             sel = "EXIT" 
                                       if sel == "CON":
                                          blob_client = container_client.get_blob_client(blob_name)
                                          stream_data = blob_client.download_blob()
                                          for chunk in stream_data.chunks():
                                              sha256.update(chunk)
                                              pbar.update(len(chunk))
                                          file_hash = sha256.hexdigest()
                                          manifest_updater_cloud(blob_name, file_hash, cur_mtime, file_size, write_now=False)
                                          move_on = True
                                          break
                                       elif sel == "CONVT" and vt_check:
                                          blob_client = container_client.get_blob_client(blob_name)
                                          stream_data = blob_client.download_blob()
                                          for chunk in stream_data.chunks():
                                              sha256.update(chunk)
                                              pbar.update(len(chunk))
                                          file_hash = sha256.hexdigest()
                                          pbar.write("\n\nPlease wait while the program checks the global virus database...")
                                          check = online_check(file_hash, blob_name, pbar, local_notif, webhook_notif, "online", blob_service_client, pref)
                                          if check == "likely_safe":
                                             manifest_updater_cloud(blob_name, file_hash, cur_mtime, file_size, write_now=False)
                                          elif check == "error":
                                             logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
                                             manifest_updater_cloud(None, None, None, None, write_now=True)
                                             with open('manifest_cloud.json', 'r') as file:
                                                           info = json.load(file)
                                                           count = len(info)
                                             logging.info(f"Successfully updated manifest_cloud.json with {count} entries, however issue with checking VT for blob {blob_name}.")
                                             pbar.write("The program ran into an error when contacting the VirusTotal service. Please check VT_check.log for more information.")
                                             pbar.write("The program will now exit in 5 seconds for security reasons, and will only save the blobs before this one.")
                                             time.sleep(5)
                                             exit()
                                          elif check == "rate":
                                             logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
                                             manifest_updater_cloud(None, None, None, None, write_now=True)
                                             with open('manifest_cloud.json', 'r') as file:
                                                           info = json.load(file)
                                                           count = len(info)
                                             logging.info(f"Successfully updated manifest_cloud.json with {count} entries, however issue with checking VT for blob {blob_name} due to rate limiting. ")
                                             pbar.write(f"You have either exceeded the API quota, or VirusTotal is down. Program will save previous blobs (excluding this one) and quit.")
                                             pbar.write("The program will now exit in 5 seconds for security reasons, and will only save the blobs before this one.")
                                             time.sleep(5)
                                             exit()
                                          elif check == "unexpected_error":                                             
                                             logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
                                             manifest_updater_cloud(None, None, None, None, write_now=True)
                                             with open('manifest_cloud.json', 'r') as file:
                                                           info = json.load(file)
                                                           count = len(info)
                                             logging.info(f"Successfully updated manifest_cloud.json with {count} entries, however issue with moving {blob_name} to quarantine.")
                                             pbar.write(f"Either Azure may be down, or some unexpected event caused the program to stop. Please check the manifest_cloud.log file.")
                                             pbar.write("The program will now exit in 5 seconds for security reasons, and will only save the blobs before this one.")
                                             time.sleep(5)
                                             exit()                                 
                                          elif check == "handled":
                                             pbar.clear()
                                             pbar.refresh()
                                          move_on = True
                                          break
                                       elif sel == "EXIT":
                                          with open('manifest_cloud.json', 'r') as file:
                                                           info = json.load(file)
                                                           count = len(info)
                                          logging.info(f"Successfully updated manifest_cloud.json with {count} entries, however user halted program for blob {blob_name}")
                                          manifest_updater_cloud(None, None, None, None, write_now=True)
                                          pbar.write("The program will now exit in 5 seconds for security reasons, and will only save the blobs before this one.")
                                          time.sleep(5)
                                          exit()
                                       else:
                                          if sel == "CONVT" and not vt_check:
                                             pbar.write("\n\nPlease setup VT in .env, and run mode C for setup validation.")
                                          else:
                                             pbar.write("\n\nInvalid input. Please try again.")
                                          continue
                  if move_on: #Added because it should not rehash the file if the user has already gone through the process.
                     continue   
                  blob_client = container_client.get_blob_client(blob_name)
                  stream_data = blob_client.download_blob()
                  with tqdm(total=stream_data.size, desc=f"Hashing blob {blob_name} from the cloud", colour="magenta", unit="B",  unit_scale=True, unit_divisor=1024) as pbar:
                        for chunk in stream_data.chunks():
                           sha256.update(chunk)
                           pbar.update(len(chunk))
                  file_hash = sha256.hexdigest()
                  manifest_updater_cloud(blob_name, file_hash, cur_mtime, file_size, write_now=False)
            except HttpResponseError as e:
                print(f"Azure HTTP Error {e.status_code} on file {blob_name}: {e.message}")
                logging.error(f"Azure HTTP Error {e.status_code} on {blob_name}: {e}")                  
                #https://pypi.org/project/azure-storage-blob/
                #https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-list-python
                #https://learn.microsoft.com/en-us/python/api/azure-core/azure.core.exceptions?view=azure-python
                #https://learn.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob.storagestreamdownloader?view=azure-python#azure-storage-blob-storagestreamdownloader-download-to-stream
         manifest_updater_cloud(None, None, None, None, write_now=True)
         with open('manifest_cloud.json', 'r') as file:
              info = json.load(file)
              count = len(info)
         logging.info(f"Successfully updated manifest_cloud.json with {count} entries.")
    except HttpResponseError as e:
        print(f"Azure Container Error: {e.status_code}: {e.message}")
        logging.error(f"Azure Container Error: {e.status_code}: {e}")
    except Exception as e:
        print(f"Unexpected Azure Error: {e}")
        logging.error(f"Unexpected Azure Error: {e}")
def validate(): #Because otherwise, invalid json would be accepted, so it is checked before anything.
    setup = alert_preferences("main-control")
    setup_2 = schedule_preferences("main-control")
    if not setup or not setup_2:
       print("Sorry, but the program was unable to continue because it has detected a setup issue.")
       print("Please check .env file, and run mode C to validate the alert_api_preferences.json and schedule_pref.json files.")
       print("The program will now exit in 5 seconds.")
       time.sleep(5)
       exit()
    global local_notif
    global webhook_notif
    global vt_check
    vt_check = VT_check("main-control")
    local_notif = local_notification_check("main-control")
    webhook_notif = webhook_check("main-control")
    if not os.path.exists("manifest.json") or os.path.getsize("manifest.json") == 0: 
       create_manifest("manifest.json")
    if not os.path.exists("manifest2.json") or os.path.getsize("manifest2.json") == 0: 
       create_manifest("manifest2.json") 
    if not os.path.exists("manifest_cloud.json") or os.path.getsize("manifest_cloud.json") == 0: 
       create_manifest("manifest_cloud.json")
    for i in range(1, 4):
        if i == 1:
           file = "manifest.json"
        elif i == 2:
           file = "manifest2.json"
        else:
           file = "manifest_cloud.json"
        try:
            with open(file, 'r') as f:
                 json.load(f)
        except ijson.common.IncompleteJSONError:
            logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
            print(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
            print(f"This program will exit in 5 seconds for security reasons.")
            time.sleep(5)
            exit()
        except Exception as e:
             logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
             print(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
             print(f"This program will exit in 5 seconds for security reasons.")
             time.sleep(5)
             exit()
def create_manifest(path):
    with open(path, "w") as f:
         json.dump({}, f)
def argCV():
    #Command Line Interface CLI, similar to C which makes sense.
    #considering python is an interpreted language.
    arg = argparse.ArgumentParser(description="3-2-1 Sync Done! A Data Integrity Solution", formatter_class=argparse.RawTextHelpFormatter) #class because new line wasn't working.
    arg.add_argument("--source", required=True, help="REQUIRED: Please add root directory as a string (e.g. \"C:\\Users\\Username\\Downloads\").")
    arg.add_argument("--source2", required=False, help="Optional: Add second directory to compare as a string (e.g. \"C:\\Users\\Username\\Videos\").")
    arg.add_argument("--ext", help="Optional: Only backup files by extension (as a \"string\") (e.g., \".jpg\", \".pdf\", etc.)")
    arg.add_argument("--mode", required=True, 
                     help="REQUIRED: Type the character(s) that corresponds with the respective function. " 
                     "\n[A1]: Hash, Verify, Quarantine Files."
                     "\n[A2]: Hash, Verify, and Quarantine Files using Schedule."
                     "\n[1B]: Checking the integrity of a specific file in manifest.json." 
                     "\n[2B]: Checking the integrity of a specific file in a manifest2.json" 
                     "\n[C]: Check if Local Notifications, Discord Webhook, Azure Blob Storage, and VirusTotal API are working as intended (use a random string for --source)"
                     "\n[D1]: Hash, Verify, Quarantine Blobs from Cloud. (use a random string for --source)"
                     "\n[D2]: Hash, Verify, Quarantine Blobs from Cloud using Schedule. (use a random string for --source)")
    return arg.parse_args()
def retrieve_file(target_path, manifest_data):
    if not os.path.exists(manifest_data) or os.path.getsize(manifest_data) == 0:
        print(f"Error: The manifest file '{manifest_data}' is empty or does not exist. Exiting program")
        exit()
    path = os.path.abspath(target_path)
    try:
      with open(manifest_data, 'rb') as f:
            for file_path, info in ijson.kvitems(f, ''):
               if file_path == path:
                  return info
               else:
                  continue #I fixed it, I accidently had a return statement here from the inital construction of the program.
            return None
    except ijson.common.IncompleteJSONError:
        print(f"ERROR! The manifest file {manifest_data} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
        print(f"This program will exit in 5 seconds for security reasons.")
        time.sleep(5)
        exit()
        #https://pypi.org/project/ijson/
def check_if_file_exists(file_path, manifest_data):
    #Redone, as I promised before. In the retrieve function itself.
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
       global buffer_arr #Global because buffer_arr needs to be accessed globally.
       stat = os.stat(file_path) #Just like C, with stat.
       buffer_arr[file_path] = {
               "hash": hash,
               "last_seen": datetime.now().isoformat(),
               "mtime": round(stat.st_mtime, 4), 
               "size": stat.st_size
         }
       json_writer(buffer_arr, manifest_data) 
    else:
       print(f"ALERT! {file_path} has been modified or corrupted since it was last seen!")
       logging.warning(f"{file_path} has been modified or corrupted since it was last seen.")
def total_size(directory, extension):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if extension is not None and not file.endswith(extension):
                continue
            if file in EXCLUDED:
                continue
            #Unlike my previous way, this now shows the progress bar moving according to the size of the directory.
            filepath = os.path.join(root, file)
            count += os.path.getsize(filepath)
    return count
def source_updater(root, files, pbar, pref, manifest_name, manifest_data, this_one): #I added this because I didnt like how
    #before the log accumulated all errors, so now logging is specific to the given manifest file.
    if this_one == "source":
       manifest = "manifest"
    else:
       manifest = "manifest2"
    for file in files:
        move_on = False
        if argv.ext and not file.endswith(argv.ext):
           continue
        if os.path.basename(file) in EXCLUDED:
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
              pbar.update(cur_size)
              pbar.refresh() 
              continue
        hash_calc = hash256_caller(file_path)
        if hash_calc:
           status = hash_compare(file_path, hash_calc, manifest_data)
           if "new" in status: 
                manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
                pbar.update(cur_size)
           elif "corrupted" in status:
                 if local_notif:
                    try:
                      alert_sound()
                      notification.notify(
                           title="Corrupted File Warning!",
                           message=f"{file} has been changed or is corrupted, please select an option in the program!",
                           app_name="3-2-1-Sync-Done!",
                           timeout=5
                      )
                    except Exception:
                           pass  
                 pbar.clear()
                 pbar.write(f"WARNING! This file {file} has been changed or corrupted!")
                 pbar.refresh() 
                 while True:
                     if pref is None:
                        pbar.write("Type 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ")
                        pbar.refresh() 
                        sel = input(" ").strip().upper()
                     else:
                        if pref == "manual":
                           pbar.write("Type 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ")
                           pbar.refresh() 
                           sel = input(" ").strip().upper()
                        elif pref == "false":
                           sel = "CON"
                        elif pref == "true":
                           sel = "CONVT"
                        else:
                           pbar.write("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                           logging.warning("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                           sel = "EXIT" 
                     if sel == "CON":
                        manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
                        pbar.update(cur_size)
                        pbar.refresh() 
                        move_on = True
                        break
                     elif sel == "CONVT" and vt_check:
                        pbar.write("\n\nPlease wait while the program checks the global virus database...")
                        virus_check = online_check(hash_calc, file_path, pbar, local_notif, webhook_notif, "local", None, pref)
                        if virus_check == "likely_safe":
                           manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
                           pbar.update(cur_size)
                           move_on = True
                        elif virus_check == "rate":
                           logging.basicConfig(level=logging.INFO, filename=f"{manifest}.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
                           manifest_updater(None, None, write_now=True, which_one=this_one)
                           with open(f'{manifest}.json', 'r') as file:
                                info = json.load(file)
                                count = len(info)
                           logging.info(f"Successfully updated {manifest}.json with {count} entries, however issue with checking VT for file {file_path} due to rate limiting. ")
                           pbar.write(f"You have either exceeded the API quota, or VirusTotal is down. Program will save previous files (excluding this one) and quit.")
                           pbar.write("The program will now exit in 5 seconds for security reasons, and will only save the files before this one.")
                           time.sleep(5)
                           exit()   
                        elif virus_check == "error":
                           logging.basicConfig(level=logging.INFO, filename=f"{manifest}.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
                           manifest_updater(None, None, write_now=True, which_one=this_one)
                           with open(f'{manifest}.json', 'r') as file:
                                 info = json.load(file)
                                 count = len(info)
                           logging.info(f"Successfully updated {manifest} with {count} entries, however issue with checking VT for file {file_path}.")
                           pbar.write("The program ran into an error when contacting the VirusTotal service. Please check VT_check.log for more information.")
                           pbar.write("The program will now exit in 5 seconds for security reasons, and will only save the files before this one.")
                           time.sleep(5)
                           exit()
                        elif "handled":
                             pbar.clear()
                             pbar.write(f"The suspicious file {file_path} was moved to the quarantine container. Continuing program operation...")
                             pbar.update(cur_size)
                             pbar.refresh()
                             move_on = True
                        break
                     elif sel == "EXIT":
                        pbar.write(f"\n\nProgram quitting for data integrity purposes. Please check {manifest_name}.log")
                        logging.basicConfig(level=logging.INFO, filename=f"{manifest}.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
                        manifest_updater(None, None, write_now=True, which_one=this_one)
                        with open(f'{manifest}.json', 'r') as file:
                                 info = json.load(file)
                                 count = len(info)
                        logging.info(f"Successfully updated {manifest} with {count} entries, however user halted program for file {file_path}")
                        pbar.write("The program will now exit in 5 seconds for security reasons, and will only save the files before this one.")
                        exit()
                     else:
                        if sel == "CONVT" and not vt_check:
                           pbar.write("\n\nPlease setup VT check in .env, and run mode C for setup validation.")
                        else:
                           pbar.write("\n\nInvalid input. Please try again.")
                        continue
                 if move_on:
                    continue
           elif "same" in status:
                manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
                pbar.update(cur_size)
        else:
          pbar.write(f"FAILURE: The following file {file} could not be hashed. Please check {manifest_name}.log for information.")  
          pbar.update(cur_size)
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
        elif which_one == "target":
           json_writer(buffer_arr,"manifest2.json")
        buffer_arr = {}
def manifest_updater_cloud(blob, hash, modified, size, write_now):
   global buffer_arr
   if (blob and hash) and blob not in EXCLUDED:
      buffer_arr[blob] = {
                  "hash": hash,
                  "last_seen": datetime.now().isoformat(),
                  "mtime": modified,
                  "size": size
      }
   if ((len(buffer_arr) % BATCH_SIZE == 0) or write_now) and buffer_arr: 
      json_writer(buffer_arr, "manifest_cloud.json")
      buffer_arr = {}
@catch_exceptions(cancel_on_failure=True)
def a_mode(pref):
       global buffer_arr
       logging.basicConfig(level=logging.INFO, filename="manifest.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
       #Using force, I was able to get the program to force logging correctly, because the logger ignores this unless its forced.
       print("Please wait while the program discovers the total size of the directory in bytes...")
       total = total_size(argv.source, argv.ext)
       manifest_source = load_manifest("manifest.json")
       with tqdm(total=total, desc="Hashing files, please wait", colour="green", unit="B", unit_scale=True, unit_divisor=1024) as pbar:
             for root, dirs, files in os.walk(argv.source):
                source_updater(root, files, pbar, pref, manifest_name="manifest", manifest_data=manifest_source, this_one="source")
       manifest_updater(None, None, write_now=True, which_one="source")
       with open('manifest.json', 'r') as file:
                     info = json.load(file)
                     count = len(info)
       logging.info(f"Successfully updated manifest.json with {count} entries.")
       if argv.source2: #Because it would crash, for obvious reasons.
          logging.basicConfig(level=logging.INFO, filename="manifest2.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
          buffer_arr = {}
          print("Please wait while the program discovers the total size of the second directory in bytes...")
          total = total_size(argv.source2, argv.ext)
          manifest_target = load_manifest("manifest2.json")
          with tqdm(total=total, desc="Hashing second batch of files, please wait", colour="blue", unit="B",  unit_scale=True, unit_divisor=1024) as pbar:
             for root, dirs, files in os.walk(argv.source2):
                source_updater(root, files, pbar, pref, manifest_name="manifest2", manifest_data=manifest_target, this_one="target")
          manifest_updater(None, None, write_now=True, which_one="target")
          with open('manifest2.json', 'r') as file:
                        info = json.load(file)
                        count = len(info)
          logging.info(f"Successfully updated manifest2.json with {count} entries.")
       buffer_arr = {}
argv = argCV()
if argv.source == " " and not (argv.mode == "C" or argv.mode =="D1" or argv.mode == "D2"):
   print("ERROR: An empty string " " was provided. This is only allowed for mode C and mode D.")
   exit()
if argv.mode == "A1":
   validate()
   a_mode(None)
elif argv.mode == "A2":
   time_task = os.getenv("TIME_IN_24_HOURS")
   timezone_task = os.getenv("TIMEZONE_DST_AWARE")
   if not time_task:
      print("Error: Time not provided. Please create a .env file based on .env example")
      exit()
   if not timezone_task:
      print("Error: Timezone not provided. Please create a .env file based on .env example and pytz_timezones.txt")
      exit()
   validate()
   try:
      with open("schedule_pref.json", "r") as f:
           info = json.load(f)
      check_for_virus = info.get("virus_check") 
   except Exception as e:
      print(f"Exception: {e}")
      exit()
   schedule.every().day.at(time_task, timezone(timezone_task)).do(a_mode, check_for_virus)
   while True:
      schedule.run_pending()
      time.sleep(1)
elif (argv.mode == "1B" or argv.mode == "2B") and not argv.source2:
     validate()
     if argv.mode == "1B":
        logging.basicConfig(level=logging.INFO, filename="manifest.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
        manifest = "manifest.json"
     else:
        logging.basicConfig(level=logging.INFO, filename="manifest2.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
        manifest = "manifest2.json"
     check_if_file_exists(argv.source, manifest)
elif argv.mode == "C":
     main_menu("notify")
elif argv.mode == "D1":
     logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
     #I added this because the logging was excessive by default, so now only actual errors, not standard http request information will show up.
     logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
     logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
     #https://stackoverflow.com/questions/52051501/azure-blob-storage-sdk-switch-off-logging
     validate()
     manifest_target = load_manifest("manifest_cloud.json")
     download_blob(argv.ext, manifest_target, None)
elif argv.mode == "D2":
     time_task = os.getenv("TIME_IN_24_HOURS")
     timezone_task = os.getenv("TIMEZONE_DST_AWARE")
     if not time_task:
          print("Error: Time not provided. Please create a .env file based on .env example")
          exit()
     if not timezone_task:
          print("Error: Timezone not provided. Please create a .env file based on .env example and pytz_timezones.txt")
          exit()
     try:
         with open("schedule_pref.json", "r") as f:
              info = json.load(f)
         check_for_virus = info.get("virus_check") 
     except Exception as e:
         print(f"Exception: {e}")
         exit()
     logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
     #I added this because the logging was excessive by default, so now only actual errors, not standard http request information will show up.
     logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
     logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
     #https://stackoverflow.com/questions/52051501/azure-blob-storage-sdk-switch-off-logging
     validate()
     manifest_target = load_manifest("manifest_cloud.json")
     schedule.every().day.at(time_task, timezone(timezone_task)).do(download_blob, argv.ext, manifest_target, check_for_virus)
     while True:
       schedule.run_pending()
       time.sleep(1)   
else:
    if not argv.source2:
       print(f"{argv.mode} is not a valid mode. Please try again.")
    else:
       print(f"Please only use --source and not --source2. Thank you!")
#os.walk(): https://www.w3schools.com/python/ref_os_walk.asp
#shebang: https://realpython.com/python-shebang/ 
#Progress barhttps://tqdm.github.io/
#Scheduler: https://pypi.org/project/schedule/
#timezone: https://schedule.readthedocs.io/en/stable/timezones.html
#https://stackoverflow.com/questions/3489183/how-can-i-get-a-human-readable-timezone-name-in-python
