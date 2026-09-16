import os
import logging
import json
import shutil
import time
import questionary
import ijson
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
load_dotenv()
def create_manifest(path):
    with open(path, "w") as f_create:
         json.dump({}, f_create)
def inner_validate(file):
    if not os.path.exists(f'{file}.json') or os.path.getsize(f"{file}.json") == 0: 
       create_manifest(f"{file}.json")
    try:
        with open(f'{file}.json', 'r') as valid:
             json.load(valid)
    except ijson.common.IncompleteJSONError:
            logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
            print(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
            print("This program will exit in 5 seconds for security reasons.")
            time.sleep(5)
            exit()
    except Exception:
             logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
             print(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
             print("This program will exit in 5 seconds for security reasons.")
             time.sleep(5)
             exit()
def mover_helper(directory_2, manifest_2):
    global inner
    global break_outer
    global switch_dir
    inner = False
    break_outer = False
    switch_dir = False
    print(f"Program restarting for directory {directory_2}.")
    mover(directory_2, manifest_2)
def mover(directory, manifest):
     global inner
     global break_outer
     logging.basicConfig(level=logging.INFO, filename=f"{manifest}.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
     file_dir = Path(directory)
     dir_size = 0
     move_count = 0
     if file_dir.is_dir():
        disk_total = shutil.disk_usage(file_dir)
        dir_size = disk_total.free
     else:
        print(f"The directory {file_dir} does not exist.\nThe program will now exit in 5 seconds.")
        time.sleep(5)
        exit()
     arr = []
     failed_arr = []
     total_size = 0
     break_outer = False
     #only valid options will be shown, so if not modified then it will show up in the array, otherwise it will be labeled as Not Available: File
     try:
        try:
            if os.path.getsize(f'{manifest}.json') == 0:
               print(f"The program cannot run, as there are no entries in {manifest}.json. \nThe program will now exit in 5 seconds.")
               time.sleep(5)
               exit()
            with open(f'{manifest}.json') as f:
                  entries = json.load(f)
            if len(entries) == 0:
               print("The program cannot run, as there are no entries in manifest_cloud.json. \nThe program will now exit in 5 seconds.")
               time.sleep(5)
               exit() 
        except FileNotFoundError:
               print("The manifest could not be found by the program. The program will create a new one, and exit in 5 seconds.")
               inner_validate(manifest)
               time.sleep(5)
               exit()
        except json.JSONDecodeError:
               logging.critical(f"The manifest file {manifest}.json is corrupted, and as such, the program will not copy files for security reasons!")
               print(f"The {manifest} file {manifest}.json is corrupted, and as such, the program will not copy files for security reasons!\nThe program will now exit in 5 seconds.")
               time.sleep(5)
               exit()
        print(f"Please wait while the program checks the feasibility of moving files from the manifest {manifest}.json to the directory {file_dir}")
        for key, val in tqdm(entries.items()):
            if break_outer:
               break
            date = val.get("last_seen", "never")
            file_size = val.get("size", "-1")
            if not date or date == "never" or not file_size or file_size == "-1":
               print(f"The file {key} is missing its date/size attribute, skipping.")
               continue
            date_convert = datetime.fromisoformat(date)
            cur_date = datetime.now()
            delta = cur_date - date_convert
            delta_2 = delta.days
            if delta_2 <= 7:
               arr.append(key)
               total_size += int(file_size)
               if total_size > dir_size:
                  inner = True
                  while inner:
                     print(f"Error! There is not enough space to copy any more files to the directory {file_dir}. ")
                     print(f"Total size of files in {manifest}.json (up to this point): {total_size}.\nFree space available on disk: {dir_size}.")
                     time.sleep(5)
                     mv_file = questionary.select(
                               f"Please select an option: \nA.) Copy all files before {key} \nB.) Specify a new directory to copy files to\nC.)Exit the program",
                               choices=["A", "B", "C"]
                                ).ask()
                     if mv_file == "A":
                        arr.remove(key)
                        break_outer = True
                        inner = False
                     elif mv_file == "B":
                        switch_dir = True
                        while switch_dir:
                           directory_change = questionary.path("Please enter a path to a directory (autocomplete enabled)",
                           only_directories=True).ask()
                           if directory_change.is_dir():
                              break
                           else:
                              print("Invalid path, please try again.")
                              continue
                        mover_helper(directory_change, manifest)
                     elif mv_file == "C":
                        exit()
                     else:
                        continue
        move_op = questionary.select(
            'What would you like with the files?',
             choices=[
                  f"Copy All Files to {file_dir}",
                  f"Manually Select Files to Copy to {file_dir}",
                  "Nothing, exit the program.",
             ]).ask()
        if move_op == f"Copy All Files to {file_dir}":
           pass
        elif move_op == f"Manually Select Files to Copy to {file_dir}":
           arr = questionary.checkbox('Please select the files you would like to copy', choices=arr).ask()
        else:
           print("The program will exit in 5 seconds.")
           time.sleep(5)
           exit()
        print(f"Please wait while the program copies the files over to the directory {file_dir}")
        if len(arr) == 0:
           return
        for value in tqdm(arr):
            file_path = Path(value)
            if file_path.is_file():
               try:
                  shutil.copy2(value, file_dir)
                  move_count = move_count + 1
               except PermissionError:
                  print(f"FAILURE: Program lacks permissions to copy the file {file_path} to {file_dir}. Aborting copy.")
                  logging.critical(f"FAILURE: Program lacks permissions to copy the file {file_path} to {file_dir}. Aborting copy.")
                  failed_arr.append(value)
               except shutil.Error as e:
                  print(f"ERROR: {e}")
                  logging.critical(f"ERROR with moving {file_path} to directory {file_dir}: {e}")
                  failed_arr.append(value)    
               except OSError as e: 
                  print(f"ERROR: {e}") 
                  logging.critical(f"ERROR with moving {file_path} to directory {file_dir}: {e}")   
                  failed_arr.append(value) 
            else:
               print(f"This file {value} does not exist on the disk. Aborting copy")
               logging.warning(f"This file {value} does not exist on the disk. Aborting copy")
               failed_arr.append(value)        
     except Exception as e:
        print(f"Exception: {e}")
     logging.info(f"Successfully copied {move_count} entries to directory {file_dir}.")
     return  
def mover_2():
    total_size = 0
    move_count = 0
    arr = []
    failed_arr = []
    azure_connection_string = os.getenv("AZURE_CONNECT_STR")
    azure_container_source = os.getenv("AZURE_CONTAINER")
    azure_container_target = os.getenv("AZURE_CONTAINER_TARGET")
    if not azure_connection_string :
       print("Error: AZURE_CONNECT_STR not found. Please create a .env file based on .env example")
       return
    if not azure_container_source:
       print("Error: AZURE_CONTAINER not found. Please create a .env file based on .env example")
       return
    if not azure_container_target:
        print("Error: AZURE_CONTAINER_TARGET not found. Please create a .env file based on .env example")
        return
    try:
        if os.path.getsize('manifest_cloud.json') == 0:
           print("The program cannot run, as there are no entries in manifest_cloud.json. \nThe program will now exit in 5 seconds.")
           time.sleep(5)
           exit()
        with open('manifest_cloud.json') as f:
             entries = json.load(f)
        if len(entries) == 0:
           print("The program cannot run, as there are no entries in manifest_cloud.json. \nThe program will now exit in 5 seconds.")
           time.sleep(5)
           exit() 
    except FileNotFoundError:
           print("The manifest could not be found by the program. The program will create a new one, and exit in 5 seconds.")
           inner_validate("manifest_cloud")
           time.sleep(5)
           exit()
    except json.JSONDecodeError:
           logging.critical("The manifest file manifest_cloud.json is corrupted, and as such, the program will not copy blobs for security reasons!")
           print("The manifest file manifest_cloud.json is corrupted, and as such, the program will not copy blobs for security reasons!\nThe program will now exit in 5 seconds.")
           time.sleep(5)
           exit()
    print(f"Please wait while the program checks the feasibility of moving blobs from {azure_container_source} to the container {azure_container_target}")
    for key, val in tqdm(entries.items()):
            date = val.get("last_seen", "never")
            file_size = val.get("size", "-1")
            if not date or date == "never" or not file_size or file_size == "-1":
               print(f"The file {key} is missing its date/size attribute, skipping.")
               continue
            date_convert = datetime.fromisoformat(date)
            cur_date = datetime.now()
            delta = cur_date - date_convert
            delta_2 = delta.days
            if delta_2 <= 7:
               arr.append(key)
               total_size += int(file_size)
    move_op = questionary.select(
         'What would you like with the blobs?',
          choices=[
            f"Copy All Blobs to {azure_container_target}",
            f"Manually Select Blob to Copy to {azure_container_target}",
            "Nothing, exit the program.",
          ]).ask()
    if move_op == f"Copy All Blobs to {azure_container_target}":
       pass
    elif move_op == f"Manually Select Blob to Copy to {azure_container_target}":
       arr = questionary.checkbox('Please select the blobs you would like to Copy', choices=arr).ask()
    else:
       print("The program will exit in 5 seconds.")
       time.sleep(5)
       exit()
    if len(arr) == 0:
       return
    for blob_name in tqdm(arr):
         try:
               blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
               source = blob_service_client.get_blob_client(container=azure_container_source, blob=blob_name)
               if source.exists():
                  target_blob = blob_service_client.get_blob_client(container=azure_container_target, blob=blob_name)
                  target_blob.start_copy_from_url(source.url) 
                  move_count = move_count + 1
               else:
                  print("This blob does not exist or has been moved, skipping")
                  failed_arr.append(blob_name)
                  continue
         except HttpResponseError as e:
               print(f"Azure Container Error: {e.status_code}: {e.message}")
               logging.error(f"Azure Container Error: {e.status_code}: {e}")
               failed_arr.append(blob_name)
         except Exception as e:
               print(f"Unexpected Azure Error: {e}")
               logging.error(f"Unexpected Azure Error: {e}")
               failed_arr.append(blob_name)
    logging.info(f"Successfully copied {move_count} blobs from container {azure_container_source} to container {azure_container_target}.")
    return