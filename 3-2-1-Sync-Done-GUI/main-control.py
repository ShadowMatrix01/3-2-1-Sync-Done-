#!/usr/bin/env python3 
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
import questionary
import re
import threading #Blobs were causing GUI to freeze, so I had to introduce threading.
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
from datetime import datetime
from hashHOT import hash256_caller
from json_control import json_writer, hash_compare, load_manifest
from VT_online_check import online_check
from notify import notify_window,local_notification_check, webhook_check, vt_check, alert_preferences, alert_sound, schedule_preferences
from mover_manage import mover, mover_2
from plyer import notification
from pytz import timezone
import customtkinter as ctk
from tkinter import filedialog
load_dotenv()
BATCH_SIZE = 4096 #Constant, because the amount of IO operations was slowing down the project by a lot.
buffer_arr = {}
write_now = False
vt_check_2 = False
local_notif = False
webhook_notif = False
EXCLUDED = ["manifest.json", "manifest2.json", "manifest_cloud.json", "manifest.log", "manifest2.log", "manifest_cloud.log", "VT_check.log", "VT_online_check.py"]     
def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except Exception:
                import traceback
                app.write_box(traceback.format_exc())
                logging.critical(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator
#I could not use standard exceptions, so decorator and wrapper taken from docs for scheduler.
#https://schedule.readthedocs.io/en/stable/exception-handling.html
# noinspection DuplicatedCode
@catch_exceptions(cancel_on_failure=True)
def preventer(directory):
    os_pattern = r"^[a-zA-Z]:[/\\]|^/" #I added this because I noticed an edge case
    #when I was testing my program, so this should prevent something like C:Users/Photos
    if re.match(os_pattern, directory):
       return True
    return False
def validate(): #Because otherwise, invalid json would be accepted, so it is checked before anything.
    setup = alert_preferences(app, "main-control")
    setup_2 = schedule_preferences(app, "main-control")
    if not setup or not setup_2:
       app.write_box("Sorry, but the program was unable to continue because it has detected a setup issue.")
       app.write_box("Please check .env file, and run mode C to validate the alert_api_preferences.json and schedule_pref.json files.")
       app.write_box("The program will now exit in 5 seconds.")
       time.sleep(5)
       exit()
    global local_notif
    global webhook_notif
    global vt_check_2
    vt_check_2 = vt_check(app, "main-control")
    local_notif = local_notification_check(app, "main-control")
    webhook_notif = webhook_check(app, "main-control")
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
            with open(file, 'r') as valid:
                 json.load(valid)
        except ijson.common.IncompleteJSONError:
            logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
            app.write_box(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
            app.write_box(f"This program will exit in 5 seconds for security reasons.")
            time.sleep(5)
            exit()
        except Exception:
             logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
             app.write_box(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
             app.write_box(f"This program will exit in 5 seconds for security reasons.")
             time.sleep(5)
             exit()
def create_manifest(path):
    with open(path, "w") as f_create:
         json.dump({}, f_create)
@catch_exceptions(cancel_on_failure=True)
def source_updater_helper(app, status3, pbar, manifest_file_2, file_name_2, this_one_2):
   logging.basicConfig(level=logging.INFO, filename=f"{manifest_file_2}.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
   manifest_updater(None, None, write_now_updater=True, which_one=this_one_2)
   with open(f'{manifest_file_2}.json', 'r') as file_source:
        log_msg = ""
        pbar_msg_1 = ""
        pbar_msg_2 = "The program will now exit in 5 seconds for security reasons, and will only save the files before this one."
        info_source = json.load(file_source)
        count = len(info_source) 
        match status3:
            case "error":
                log_msg = f"Successfully updated {manifest_file_2}.json with {count} entries, however issue with checking VT for file {file_name_2}."
                pbar_msg_1 = "The program ran into an error when contacting the VirusTotal service. Please check VT_check.log for more information."
            case "rate":
                log_msg = f"Successfully updated {manifest_file_2}.json with {count} entries, however issue with checking VT for file {file_name_2} due to rate limiting. "
                pbar_msg_1 = f"You have either exceeded the API quota, or VirusTotal is down. Program will save previous files (excluding this one) and quit."    
            case "EXIT":
                log_msg = f"Program has halted for data integrity purposes. Please check {manifest_file_2}.log"
                pbar_msg_1 = "User has halted program."
            case _:
                pass
        logging.info(log_msg)
        app.write_box(pbar_msg_1)
        app.write_box(pbar_msg_2)
        time.sleep(5)
        exit()
# noinspection DuplicatedCode
def source_updater(app, root, files, pbar, pref, manifest_name, manifest_data, this_one): #I added this because I didn't like how
    #before the log accumulated all errors, so now logging is specific to the given manifest file.
    if this_one == "source":
       manifest_file = "manifest"
    else:
       manifest_file = "manifest2"
    for file in files:
        move_on = False
        if app.argv.ext and not file.endswith(app.argv.ext):
           continue
        if os.path.basename(file) in EXCLUDED:
           continue
        # noinspection bad-argument-type
        file_path = os.path.normpath(os.path.join(root, file))
        try:
            f_stat = os.stat(file_path)
            cur_mtime = round(f_stat.st_mtime, 4) #Avoids inconsistencies in floating point times.
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
                manifest_updater(file_path, hash_calc, write_now_updater=False, which_one=this_one)
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
                 app.write_box(f"WARNING! This file {file} has been changed or corrupted!")
                 pbar.refresh() 
                 while True:
                     if pref is None:
                        pbar.refresh() 
                        sel = questionary.select(
                              "Select 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ",
                               choices=["CON", "CONVT", "EXIT"]
                        ).ask()
                     else:
                        if pref == "manual":
                           pbar.refresh() 
                           sel = questionary.select(
                                 "Select 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ",
                                 choices=["CON", "CONVT", "EXIT"]
                           ).ask()
                        elif pref == "false":
                           sel = "CON"
                        elif pref == "true":
                           sel = "CONVT"
                        else:
                           app.write_box("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                           logging.warning("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                           sel = "EXIT" 
                     if sel == "CON":
                        manifest_updater(file_path, hash_calc, write_now_updater=False, which_one=this_one)
                        pbar.update(cur_size)
                        pbar.refresh() 
                        move_on = True
                        break
                     elif sel == "CONVT" and vt_check_2:
                        app.write_box("\n\nPlease wait while the program checks the global virus database...")
                        virus_check = online_check(app, hash_calc, file_path, pbar, local_notif, webhook_notif, "local", None, pref)
                        if virus_check == "likely_safe":
                           manifest_updater(file_path, hash_calc, write_now_updater=False, which_one=this_one)
                           pbar.update(cur_size)
                           move_on = True
                        elif virus_check == "rate":
                           source_updater_helper(app, virus_check, pbar, manifest_file, file_path, this_one)
                        elif virus_check == "error":
                           source_updater_helper(app, virus_check, pbar, manifest_file, file_path, this_one)
                        elif "handled":
                             pbar.clear()
                             app.write_box(f"The suspicious file {file_path} was moved to the quarantine container. Continuing program operation...")
                             pbar.update(cur_size)
                             pbar.refresh()
                             move_on = True
                        break
                     elif sel == "EXIT":
                        source_updater_helper(app, "EXIT", pbar, manifest_file, file_path, this_one)
                     else:
                        if sel == "CONVT" and not vt_check_2:
                           app.write_box("\n\nPlease setup VT check in .env, and run mode C for setup validation.")
                        else:
                           app.write_box("\n\nInvalid input. Please try again.")
                        continue
                 if move_on:
                    continue
           elif "same" in status:
                manifest_updater(file_path, hash_calc, write_now_updater=False, which_one=this_one)
                pbar.update(cur_size)
        else:
          app.write_box(f"FAILURE: The following file {file} could not be hashed. Please check {manifest_name}.log for information.")  
          pbar.update(cur_size)
def manifest_updater(file_path, hash_calc, write_now_updater, which_one):
    global buffer_arr #Global because buffer_arr needs to be accessed globally.
    if (file_path and hash_calc) and os.path.basename(file_path) not in EXCLUDED:
         stat = os.stat(file_path) #Just like C, with stat.
         buffer_arr[file_path] = {
                     "hash": hash_calc,
                     "last_seen": datetime.now().isoformat(),
                     "mtime": round(stat.st_mtime, 4), 
                     "size": stat.st_size
         }
    if ((len(buffer_arr) % BATCH_SIZE == 0) or write_now_updater) and buffer_arr: #Prevents edge case that was happening during testing.
        if which_one == "source":
           json_writer(buffer_arr,"manifest.json")
        elif which_one == "target":
           json_writer(buffer_arr,"manifest2.json")
        buffer_arr = {}
def a_mode(app, pref):
   try:
       global buffer_arr
       src_tgt = "source"
       logging.basicConfig(level=logging.INFO, filename="manifest.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
       #Using force, I was able to get the program to force logging correctly, because the logger ignores this unless its forced.
       app.write_box("Please wait while the program discovers the total size of the directory in bytes...")
       total = total_size(app.argv.source, app.argv.ext)
       manifest_source = load_manifest("manifest.json")
       with CTkProgress(app,total=total,desc="Hashing files, please wait") as pbar:
             for root, dirs, files in os.walk(app.argv.source):
                source_updater(app, root, files, pbar, pref, manifest_name="manifest", manifest_data=manifest_source, this_one=src_tgt)
       manifest_updater(None, None, write_now_updater=True, which_one=src_tgt)
       with open('manifest.json', 'r') as file:
                     info_a = json.load(file)
                     count = len(info_a)
       logging.info(f"Successfully updated manifest.json with {count} entries.")
       if app.argv.source2: #Because it would crash, for obvious reasons.
          src_tgt = "target"
          logging.basicConfig(level=logging.INFO, filename="manifest2.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
          buffer_arr = {}
          app.write_box("Please wait while the program discovers the total size of the second directory in bytes...")
          total = total_size(app.argv.source2, app.argv.ext)
          manifest_target_a = load_manifest("manifest2.json")
          with CTkProgress(app,total=total,desc="Hashing second batch of files, please wait") as pbar:
             for root, dirs, files in os.walk(app.argv.source2):
                source_updater(app, root, files, pbar, pref, manifest_name="manifest2", manifest_data=manifest_target_a, this_one=src_tgt)
          manifest_updater(None, None, write_now_updater=True, which_one=src_tgt)
          with open('manifest2.json', 'r') as file:
                        info_a = json.load(file)
                        count = len(info_a)
          logging.info(f"Successfully updated manifest2.json with {count} entries.")
       buffer_arr = {}
   except KeyboardInterrupt:
          manifest_source_or_target = "manifest" if src_tgt == "source" else "manifest2"
          try:
             app.write_box("Signal interrupt detected, saving previous files to manifest...")
             manifest_updater(None, None, write_now_updater=True, which_one=src_tgt)
             with open(f'{manifest_source_or_target}.json', 'r') as file:
                           info_blob = json.load(file)
                           count = len(info_blob)
             logging.info(f"Successfully updated {manifest_source_or_target}.json with {count} entries.")
          except Exception as k:
            app.write_box(f"Fatal Exception with trying to save files to {manifest_source_or_target}.json: {k}")
            logging.critical(f"Fatal Exception with trying to save blobs to {manifest_source_or_target}: {k}")
          exit() 
def total_size(directory, extension):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if extension is not None and not file.endswith(extension):
                continue
            if file in EXCLUDED:
                continue
            #Unlike my previous way, this now shows the progress bar moving according to the size of the directory.
            # noinspection bad-argument-type
            filepath = os.path.join(root, file)
            count += os.path.getsize(filepath)
    return count  
def download_blob(app, extension, manifest_data, pref):
    global buffer_arr
    buffer_arr = {}
    azure_connection_string = os.getenv("AZURE_CONNECT_STR")
    azure_container_name = os.getenv("AZURE_CONTAINER")
    if not azure_connection_string :
       app.write_box("Error: AZURE_CONNECT_STR not found. Please create a .env file based on .env example")
       return
    if not azure_container_name:
       app.write_box("Error: AZURE_CONTAINER not found. Please create a .env file based on .env example")
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
                     with CTkProgress(app,total=file_size,desc=f"Verifying blob {blob_name} from cloud vs local") as pbar:  
                              data = manifest_data[blob_name]
                              mtime = data.get("mtime")
                              if mtime == cur_mtime and data.get("size") == file_size:
                                 blob_hash = data.get("hash")
                                 manifest_updater_cloud(blob_name, blob_hash, cur_mtime, file_size, write_now_cloud=False)
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
                                 app.write_box(f"WARNING! The blob {blob_name} has been changed or corrupted!")
                                 pbar.refresh() 
                                 while True:
                                       if pref is None:
                                          pbar.refresh() 
                                          sel = questionary.select(
                                                "Select 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ",
                                                 choices=["CON", "CONVT", "EXIT"]
                                          ).ask()
                                       else:
                                          if pref == "manual":
                                             pbar.refresh() 
                                             sel = questionary.select(
                                                   "Select 'CON' to update manifest with new hash (NO VT CHECK), 'CONVT' to update manifest with VT check, or 'EXIT' to abort program: ",
                                                   choices=["CON", "CONVT", "EXIT"]
                                             ).ask()
                                          elif pref == "false":
                                             sel = "CON"
                                          elif pref == "true":
                                             sel = "CONVT"
                                          else:
                                             app.write_box("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                                             logging.warning("schedule_pref.json has an invalid value for virus_check, please check file. Accepted values \"manual\", \"false\", \"true\". ")
                                             sel = "EXIT" 
                                       if sel == "CON":
                                          blob_client = container_client.get_blob_client(blob_name)
                                          stream_data = blob_client.download_blob()
                                          for chunk in stream_data.chunks():
                                              sha256.update(chunk)
                                              pbar.update(len(chunk))
                                          file_hash = sha256.hexdigest()
                                          manifest_updater_cloud(blob_name, file_hash, cur_mtime, file_size, write_now_cloud=False)
                                          move_on = True
                                          break
                                       elif sel == "CONVT" and vt_check_2:
                                          blob_client = container_client.get_blob_client(blob_name)
                                          stream_data = blob_client.download_blob()
                                          for chunk in stream_data.chunks():
                                              sha256.update(chunk)
                                              pbar.update(len(chunk))
                                          file_hash = sha256.hexdigest()
                                          app.write_box("\n\nPlease wait while the program checks the global virus database...")
                                          check = online_check(app, file_hash, blob_name, pbar, local_notif, webhook_notif, "online", blob_service_client, pref)
                                          if check == "likely_safe":
                                             manifest_updater_cloud(blob_name, file_hash, cur_mtime, file_size, write_now_cloud=False)
                                          elif check == "error":
                                             blob_updater_helper(app, check, pbar, blob_name)
                                          elif check == "rate":
                                             blob_updater_helper(app, check, pbar, blob_name)
                                          elif check == "unexpected_error":                                             
                                             blob_updater_helper(app, check, pbar, blob_name)
                                          elif check == "handled":
                                             pbar.clear()
                                             pbar.refresh()
                                          move_on = True
                                          break
                                       elif sel == "EXIT":
                                            blob_updater_helper(app, "EXIT", pbar, blob_name)
                                       else:
                                          if sel == "CONVT" and not vt_check_2:
                                             app.write_box("\n\nPlease setup VT in .env, and run mode C for setup validation.")
                                          else:
                                             app.write_box("\n\nInvalid input. Please try again.")
                                          continue
                  if move_on: #Added because it should not rehash the file if the user has already gone through the process.
                     continue   
                  blob_client = container_client.get_blob_client(blob_name)
                  stream_data = blob_client.download_blob()
                  with CTkProgress(app,total=stream_data.size,desc=f"Hashing blob {blob_name} from the cloud") as pbar:
                        for chunk in stream_data.chunks():
                           sha256.update(chunk)
                           pbar.update(len(chunk))
                  file_hash = sha256.hexdigest()
                  manifest_updater_cloud(blob_name, file_hash, cur_mtime, file_size, write_now_cloud=False)
            except HttpResponseError as e_blob:
                app.write_box(f"Azure HTTP Error {e_blob.status_code} on file {blob_name}: {e_blob.message}")
                logging.error(f"Azure HTTP Error {e_blob.status_code} on {blob_name}: {e_blob}")
                #https://pypi.org/project/azure-storage-blob/
                #https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-list-python
                #https://learn.microsoft.com/en-us/python/api/azure-core/azure.core.exceptions?view=azure-python
                #https://learn.microsoft.com/en-us/python/api/azure-storage-blob/azure.storage.blob.storagestreamdownloader?view=azure-python#azure-storage-blob-storagestreamdownloader-download-to-stream
         manifest_updater_cloud(None, None, None, None, write_now_cloud=True)
         with open('manifest_cloud.json', 'r') as file:
              info_blob = json.load(file)
              count = len(info_blob)
         logging.info(f"Successfully updated manifest_cloud.json with {count} entries.")
    except KeyboardInterrupt:
       try:
          app.write_box("Signal interrupt detected, saving previous blobs to manifest...")
          manifest_updater_cloud(None, None, None, None, write_now_cloud=True)
          with open('manifest_cloud.json', 'r') as file:
                        info_blob = json.load(file)
                        count = len(info_blob)
          logging.info(f"Successfully updated manifest_cloud.json with {count} entries.")
       except Exception as k:
         app.write_box(f"Fatal Exception with trying to save blobs to manifest_cloud.json: {k}")
         logging.critical(f"Fatal Exception with trying to save blobs to manifest_cloud.json: {k}")
       exit()
    except HttpResponseError as e_blob:
        app.write_box(f"Azure Container Error: {e_blob.status_code}: {e_blob.message}")
        logging.error(f"Azure Container Error: {e_blob.status_code}: {e_blob}")
    except Exception as e_blob:
        app.write_box(f"Unexpected Error: {e_blob}")
        logging.error(f"Unexpected Error: {e_blob}")
def retrieve_file(target_path, manifest_data):
    if not os.path.exists(manifest_data) or os.path.getsize(manifest_data) == 0:
        app.write_box(f"Error: The manifest file '{manifest_data}' is empty or does not exist. Exiting program")
        exit()
    path = os.path.abspath(target_path)
    try:
      with open(manifest_data, 'rb') as f2:
            for file_path, info2 in ijson.kvitems(f2, ''):
               if file_path == path:
                  return info2
               else:
                  continue #I fixed it, I accidentally had a return statement here from the initial construction of the program.
            return None
    except ijson.common.IncompleteJSONError:
        app.write_box(f"ERROR! The manifest file {manifest_data} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
        app.write_box(f"This program will exit in 5 seconds for security reasons.")
        time.sleep(5)
        exit()
        #https://pypi.org/project/ijson/
def check_if_file_exists(file_path, manifest_data):
    #Redone, as I promised before. In the retrieve function itself.
    check = retrieve_file(file_path, manifest_data)
    if not check:
       app.write_box(f"Sorry, but {file_path} was not found in {manifest_data}")
       return
    if not os.path.exists(file_path):
       app.write_box(f"ALERT! {file_path} was not found on the disk.")
       app.write_box(f"\nLast known hash: {check['hash']}\nLast seen: {check['last_seen']}\nLast known modified time: {check['mtime']}\nLast known size: {check['size']} bytes.")
       logging.critical(f"ALERT! {file_path} was not found on the disk.\nLast known hash: {check['hash']}\nLast seen: {check['last_seen']}\nLast known modified time: {check['mtime']}\nLast known size: {check['size']} bytes.")
       return
    hash_file = hash256_caller(file_path)
    if hash_file == check['hash']:
       app.write_box(f"The file {file_path} was successfully verified. No changes have been detected from the manifest.")
       global buffer_arr #Global because buffer_arr needs to be accessed globally.
       stat = os.stat(file_path) #Just like C, with stat.
       buffer_arr[file_path] = {
               "hash": hash_file,
               "last_seen": datetime.now().isoformat(),
               "mtime": round(stat.st_mtime, 4), 
               "size": stat.st_size
         }
       json_writer(buffer_arr, manifest_data) 
    else:
       app.write_box(f"ALERT! {file_path} has been modified or corrupted since it was last seen!")
       logging.warning(f"{file_path} has been modified or corrupted since it was last seen.")
def blob_updater_helper(app, status2, pbar, blob_name_2):
    log_msg = ""
    pbar_msg_1 = ""
    pbar_msg_2 = "The program will now exit in 5 seconds for security reasons, and will only save the blobs before this one."
    logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
    try:
        manifest_updater_cloud(None, None, None, None, write_now_cloud=True)
        with open('manifest_cloud.json', 'r') as file:
            info_blob = json.load(file)
            count = len(info_blob)
        match status2:
            case "error":
                log_msg = f"Successfully updated manifest_cloud.json with {count} entries, however issue with checking VT for blob {blob_name_2}."
                pbar_msg_1 = "The program ran into an error when contacting the VirusTotal service. Please check VT_check.log for more information."
            case "rate":
                log_msg = f"Successfully updated manifest_cloud.json with {count} entries, however issue with checking VT for blob {blob_name_2} due to rate limiting. "
                pbar_msg_1 = f"You have either exceeded the API quota, or VirusTotal is down. Program will save previous blobs (excluding this one) and quit."
            case "unexpected_error":
                log_msg = f"Successfully updated manifest_cloud.json with {count} entries, however issue with moving {blob_name_2} to quarantine."
                pbar_msg_1 = f"Either Azure may be down, or some unexpected event caused the program to stop. Please check the manifest_cloud.log file."
            case "EXIT":
                log_msg = f"Successfully updated manifest_cloud.json with {count} entries, however user halted program for blob {blob_name_2}"
                pbar_msg_1 = "User has halted program."
            case _:
                pass
        logging.info(log_msg)
        app.write_box(pbar_msg_1)
        app.write_box(pbar_msg_2)
        time.sleep(5)
        exit()
    except Exception as e_write:
        app.write_box(f"Unexpected Error: {e_write}")
        logging.error(f"Unexpected Error: {e_write}")
def manifest_updater_cloud(blob, hash_cloud, modified, size, write_now_cloud):
   global buffer_arr
   if (blob and hash_cloud) and blob not in EXCLUDED:
      buffer_arr[blob] = {
                  "hash": hash_cloud,
                  "last_seen": datetime.now().isoformat(),
                  "mtime": modified,
                  "size": size
      }
   if ((len(buffer_arr) % BATCH_SIZE == 0) or write_now_cloud) and buffer_arr:
      json_writer(buffer_arr, "manifest_cloud.json")
      buffer_arr = {}
class CTkProgress:
    def __init__(self, app, total=0, desc=""):
        self.app = app
        self.total = total
        self.current = 0
        self.desc = desc
        self.app.after(0, self._initialize)
    def _initialize(self):
        self.app.progress_bar.set(0)
        self.app.progress_label.configure(text=self.desc)
    def update(self, amount):
        self.current += amount
        if self.total > 0:
            progress = min(self.current / self.total, 1.0)
        else:
            progress = 0
        percentage = progress * 100
        self.app.after(
        0,
        lambda prog=progress, perc=percentage:
        (
            self.app.progress_bar.set(prog),
            self.app.progress_label.configure(
                text=f"{self.desc} {perc:.1f}%"
            )
        )
    )
    def refresh(self):
        pass
    def write(self, message):
        self.app.after(
            0,
            lambda: self.app.progress_label.configure(text=message)
        )
    def clear(self):
        self.app.after(
            0,
            lambda: self.app.progress_label.configure(text="")
        )
    def close(self):
        self.app.after(
            0,
            lambda: self.app.progress_bar.set(0)
        )
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
class Argv:
    def __init__(self, mode=" ", source=" ", source2=" ", ext=" "):
        self.mode = mode
        self.source = source
        self.source2 = source2
        self.ext = ext
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("900x500")
        self.title("3-2-1-Sync-Done!")
        ctk.set_appearance_mode("dark")
        #https://customtkinter.tomschimansky.com/documentation/color/ Added because it was unreadable in light mode.
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(
            row=0,
            column=0,
            columnspan=2,
            rowspan=7,
            sticky="nsew"
        )
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(1, weight=1)
        self.header_label = ctk.CTkLabel(
            master=self.left_frame, 
            text="3-2-1 Sync Done! A Data Integrity Solution", 
            font=("Helvetica", 20, "bold"), 
            text_color="#ffffff"      
        )
        self.dropdown = ctk.CTkOptionMenu(
                master=self.left_frame,
                values=["Mode A1", "Mode A2", "Mode 1B", "Mode 2B", "Mode C", "Mode D1", "Mode D2", "Mode E1", "Mode E2", "Mode E3"],
                command=self.mode_return
                )
        self.dropdown.grid(row=4, column=0, padx=20, pady=20, sticky="w")
        self.dropdown.set("Mode A1") #Added to prevent edge case that was crashing the program.
        self.header_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 20), sticky="ew")
        self.grid_rowconfigure(1, weight=1)  
        self.textbox = ctk.CTkTextbox(master=self.left_frame, width=400, corner_radius=0, wrap="word")
        self.textbox.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.textbox.insert("0.0", "3--2-1 Sync Done! A Data Integrity Solution" 
                            "\n<-----------Overview of Modes and Functionality----------->"
                             "\n[A1]: Hash, Verify, Quarantine Files."
                             "\n[A2]: Hash, Verify, and Quarantine Files using Schedule."
                             "\n[1B]: Checking the integrity of a specific file in manifest.json." 
                             "\n[2B]: Checking the integrity of a specific file in a manifest2.json" 
                             "\n[C]: Check if Local Notifications, Discord Webhook, Azure Blob Storage, and VirusTotal API are working."
                             "\n[D1]: Hash, Verify, Quarantine Blobs from Cloud."
                             "\n[D2]: Hash, Verify, Quarantine Blobs from Cloud using Schedule."
                             "\n[E1]: Copy files from manifest.json to a given directory."
                             "\n[E2]: Copy files from manifest2.json to a given directory."
                             "\n[E3]: Copy blobs from manifest_cloud.json to a target container.")
        self.textbox.configure(state="disabled")
        self.argv = Argv(mode="Mode A1", source=None, source2=None, ext=None)
        self.button = ctk.CTkButton(self.left_frame, text="Start!", command=self.submit)
        self.button.grid(row=4,column=1, padx=20, pady=20, sticky="e")
        self.button.configure(state="disabled")
        self.progress_bar = ctk.CTkProgressBar(self.left_frame,  progress_color="green")
        self.progress_bar.set(0)
        self.progress_bar.grid(
         row=5,
         column=0,
         columnspan=2,
         padx=20,
         pady=(0, 20),
         sticky="ew"
        )
        self.progress_label = ctk.CTkLabel(
         self.left_frame,
         text="Waiting to hash/verify/copy file(s)/blob(s)..."
        )
        self.progress_label.grid(
         row=6,
         column=0,
         columnspan=2,
         padx=20,
         pady=(0, 10)
        )
        self.dir_label = ctk.CTkFrame(
           self.left_frame,
           border_width=2,
           border_color="#D4AF37",
           corner_radius=0,
           fg_color="transparent"
        )
        self.dir_label.grid(
           row=2,
           column=0,
           columnspan=2,
           padx=0,
           pady=(5, 0),
           sticky="nsew"
         )
        self.dir_label.grid_columnconfigure(0, weight=0)
        self.dir_label.grid_columnconfigure(1, weight=1)
        self.dir_label.grid_rowconfigure(0, weight=1)
        self.browse_button = ctk.CTkButton(
            self.dir_label,
            text="Browse",
            width=80,
            command=self.folder_directory_a
        )
        self.browse_button.grid(
         row=0,
         column=0,
         padx=(10, 5),
         pady=5,
         sticky="w"
         )
        self.selected_label = ctk.CTkEntry(self.dir_label, placeholder_text="Source: No Directory Selected")
        self.selected_label.grid(
         row=0,
         column=1,
         padx=(0, 10),
         pady=5,
         sticky="nsew"
         )
        self.message_box = ctk.CTkTextbox(self, width=280,corner_radius=0, wrap="word")
        self.message_box.grid(
         row=0,
         column=2,
         rowspan=7,
         padx=(0, 0),
         pady=0,
         sticky="nsew"
        )
        self.grid_columnconfigure(2, weight=1)
        msg = "When the program runs, you will see relevant information here. \nTo temporarily check previous events, scroll up. \nTo view and analyze program events across different dates and times, please check the relevant log file."
        self.message_box.insert("end", "\n" + msg)
        self.message_box.configure(state="disabled")
        self.dir_label_2 = ctk.CTkFrame(
           self.left_frame,
           border_width=2,
           border_color="#0032F9",
           corner_radius=0,
           fg_color="transparent"
        )
        self.dir_label_2.grid(
           row=3,
           column=0,
           columnspan=2,
           padx=0,
           pady=(5, 0),
           sticky="nsew"
        )
        self.dir_label_2.grid_columnconfigure(0, weight=0)
        self.dir_label_2.grid_columnconfigure(1, weight=1)
        self.dir_label_2.grid_rowconfigure(0, weight=1)
        self.browse_button_2 = ctk.CTkButton(
           self.dir_label_2,
           text="Browse",
           width=80,
           command=self.folder_directory_b
        )
        self.browse_button_2.grid(
         row=0,
         column=0,
         padx=(10, 5),
         pady=5,
         sticky="w"
        )
        self.selected_label_2 = ctk.CTkEntry(self.dir_label_2, placeholder_text="Source2: No Directory Selected")
        self.selected_label_2.grid(
         row=0,
         column=1,
         padx=(0, 10),
         pady=5,
         sticky="nsew"
         )
    def write_box(self, message):
        self.after(
                0,
                lambda: (
                self.message_box.configure(state="normal"),
                self.message_box.insert("end", "\n" + message),
                self.message_box.see("end"),
                self.message_box.configure(state="disabled")
                )
        )
    def folder_directory_a(self):
        folder_path = filedialog.askdirectory(initialdir="/", title="Please select a directory.")
        if folder_path:
           self.button.configure(state="normal")
           self.argv.source = folder_path
           self.selected_label.delete(0, "end")
           self.selected_label.insert(0, folder_path)
        else:
           self.argv.source = None
           self.selected_label.delete(0, "end")
           self.button.configure(state="disabled")
           return False 
    def folder_directory_b(self):
        folder_path = filedialog.askdirectory(initialdir="/", title="Please select a directory.")
        if folder_path:
           self.argv.source2 = folder_path
           self.selected_label_2.delete(0, "end")
           self.selected_label_2.insert(0, folder_path)
        else:
           self.argv.source2 = None
           self.selected_label_2.delete(0, "end")
           return False 
    def mode_return(self, value):
        self.button.configure(state="disabled")
        self.argv.mode = value
        if value == "Mode A1" or value == "Mode A2" or value=="Mode E1" or value=="Mode E2":
           pass
        elif value == "Mode 1B" or value == "Mode 2B":
           pass
        else:
           self.button.configure(state="normal")
    def mode(self):
        self.dropdown.grid()
    def file_path(self):
        file_path = filedialog.askopenfilename()
        if file_path:
           self.button.configure(state="normal")
           self.argv.source = file_path
           self.selected_label.delete(0, "end")
           self.selected_label.insert(0, file_path)
        else:
           self.argv.source = None
           self.selected_label.delete(0, "end")
           self.selected_label.insert(0, "Please Select a Valid File")
           self.button.configure(state="disabled")
           return False
    def submit(self):
        #This prevents the user from accidentally running another thread,
        #since I noticed this behavior, when I was trying to run my program.
        if getattr(self, "_job_running", False):
           return 
        self._job_running = True
        self.button.configure(state="disabled")
        threading.Thread(target=self._run_handler, daemon=True).start()
    def _run_handler(self):
        #Even when the program ran succesfully, tkinter would crash when I attempted to clean up assets normally, because
        #tkinter is not thread safe, so it must be handled accordingly.
        try:
            self.run()
        finally:
            self._job_running = False
            self.after(0, lambda: self.button.configure(state="normal"))
    def safe_destroy(self):
        #Handles safe destruction of tkinter gui.
        try:
           self.destroy()
        except Exception:
           pass
    def run(self):
      if app.argv.source is None:
          if app.argv.mode not in ["Mode C", "Mode D1", "Mode D2", "Mode E3"]:
             app.write_box(f"ERROR: {app.argv.mode} requires a source argument.")
             return
      if app.argv.mode == "Mode A1":
         test = preventer(app.argv.source)
         if app.argv.source2:
            test2 = preventer(app.argv.source2)
         else:
            test2 = True
         if not test or not test2:
            app.write_box("Error: Invalid format for directory. Valid example (Windows) C:/Users/Downloads or C:\\Users\\Downloads")
            exit()
         validate()
         a_mode(app, None)
         app.write_box(f"Program finished at {datetime.now()}")
         self.after(0, self.safe_destroy)
      elif app.argv.mode == "Mode A2": 
         test = preventer(app.argv.source)
         if app.argv.source2:
            test2 = preventer(app.argv.source2)
         else:
            test2 = True
         if not test or not test2:
            app.write_box("Error: Invalid format for directory. Valid example (Windows) C:/Users/Downloads or C:\\Users\\Downloads")
            exit()
         time_task = os.getenv("TIME_IN_24_HOURS_LOCAL")
         timezone_task = os.getenv("TIMEZONE_DST_AWARE")
         if not time_task:
            app.write_box("Error: Time not provided. Please create a .env file based on .env example")
            exit()
         if not timezone_task:
            app.write_box("Error: Timezone not provided. Please create a .env file based on .env example and pytz_timezones.txt")
            exit()
         validate()
         try:
            with open("schedule_pref.json", "r") as f:
               info = json.load(f)
            check_for_virus = info.get("virus_check") 
         except Exception as e:
            app.write_box(f"Exception: {e}")
            exit()
         schedule.every().day.at(time_task, timezone(timezone_task)).do(a_mode, app, check_for_virus)
         app.write_box(f"Mode A2 scheduled successfully for {time_task} ({timezone_task}).")
         try:
            while True:
               schedule.run_pending()
               time.sleep(1)
         except KeyboardInterrupt:
            app.write_box(f"Program finished at {datetime.now()}")
            app.write_box("Shutting down scheduler...")
            exit()
      elif (app.argv.mode == "Mode 1B" or app.argv.mode == "Mode 2B") and not app.argv.source2:
         validate()
         if app.argv.mode == "Mode 1B":
            logging.basicConfig(level=logging.INFO, filename="manifest.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
            manifest = "manifest.json"
         else:
            logging.basicConfig(level=logging.INFO, filename="manifest2.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
            manifest = "manifest2.json"
         check_if_file_exists(app.argv.source, manifest)
         app.write_box(f"Program finished at {datetime.now()}")
         self.after(0, self.safe_destroy)
      elif app.argv.mode == "Mode C":
         self.withdraw()
         self.mode_c_window = notify_window(self)
         #main_menu(app, "notify")
         #app.write_box(f"Program finished at {datetime.now()}")
         #self.after(0, self.safe_destroy)
      elif app.argv.mode == "Mode D1":
         logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
         #I added this because the logging was excessive by default, so now only actual errors, not standard http request information will show up.
         logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
         logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
         #https://stackoverflow.com/questions/52051501/azure-blob-storage-sdk-switch-off-logging
         validate()
         manifest_target = load_manifest("manifest_cloud.json")
         download_blob(app, app.argv.ext, manifest_target, None)
         app.write_box(f"Program finished at {datetime.now()}")
         self.after(0, self.safe_destroy)
      elif app.argv.mode == "Mode D2":
         time_task = os.getenv("TIME_IN_24_HOURS_CLOUD")
         timezone_task = os.getenv("TIMEZONE_DST_AWARE")
         if not time_task:
               app.write_box("Error: Time not provided. Please create a .env file based on .env example")
               exit()
         if not timezone_task:
               app.write_box("Error: Timezone not provided. Please create a .env file based on .env example and pytz_timezones.txt")
               exit()
         try:
               with open("schedule_pref.json", "r") as f:
                  info = json.load(f)
               check_for_virus = info.get("virus_check") 
         except Exception as e:
               app.write_box(f"Exception: {e}")
               exit()
         logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
         #I added this because the logging was excessive by default, so now only actual errors, not standard http request information will show up.
         logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
         logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
         #https://stackoverflow.com/questions/52051501/azure-blob-storage-sdk-switch-off-logging
         validate()
         manifest_target = load_manifest("manifest_cloud.json")
         schedule.every().day.at(time_task, timezone(timezone_task)).do(download_blob, app, app.argv.ext, manifest_target, check_for_virus)
         app.write_box(f"Mode D2 scheduled successfully for {time_task} ({timezone_task}).")
         while True:
            schedule.run_pending()
            time.sleep(1)  
      elif app.argv.mode == "Mode E1" and not app.argv.source2:
         valid = preventer(app.argv.source)
         if not valid:
               app.write_box("Error: Invalid format for directory. Valid example (Windows) C:/Users/Downloads or C:\\Users\\Downloads")
               exit()
         mover(app, app.argv.source, "manifest")
         app.write_box(f"Program finished at {datetime.now()}")
         self.after(0, self.safe_destroy)
      elif app.argv.mode == "Mode E2" and not app.argv.source2:
         valid = preventer(app.argv.source)
         if not valid:
               app.write_box("Error: Invalid format for directory. Valid example (Windows) C:/Users/Downloads or C:\\Users\\Downloads")
               exit()
         mover(app, app.argv.source, "manifest2")
         app.write_box(f"Program finished at {datetime.now()}")
         self.after(0, self.safe_destroy)
      elif app.argv.mode == "Mode E3" and (not app.argv.source and not app.argv.source2):
         logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
         logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
         logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
         mover_2(app)
         app.write_box(f"Program finished at {datetime.now()}")
         self.after(0, self.safe_destroy)
      else:
         if not app.argv.source2:
            app.write_box(f"{app.argv.mode} is not a valid mode. Please try again.")
         else:
            app.write_box(f"Please only use --source and not --source2. Thank you!")
         app.write_box(f"Program finished at {datetime.now()}") 
         self.after(0, self.safe_destroy)
app = App()
app.mainloop()
#os.walk(): https://www.w3schools.com/python/ref_os_walk.asp
#shebang: https://realpython.com/python-shebang/ 
#Progress barhttps://tqdm.github.io/
#Scheduler: https://pypi.org/project/schedule/
#timezone: https://schedule.readthedocs.io/en/stable/timezones.html
#https://stackoverflow.com/questions/3489183/how-can-i-get-a-human-readable-timezone-name-in-python