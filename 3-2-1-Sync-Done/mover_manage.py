import os
import logging
import json
import shutil
import time
import questionary
import ijson
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
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
        except FileNotFoundError:
               print("The manifest could not be found by the program. The program will create a new one, and exit in 5 seconds.")
               inner_validate(manifest)
               time.sleep(5)
               exit()
        except json.JSONDecodeError:
               logging.critical(f"The manifest file {manifest}.json is corrupted, and as such, the program will not move files for security reasons!")
               print(f"The {manifest} file {manifest}.json is corrupted, and as such, the program will not move files for security reasons!\nThe program will now exit in 5 seconds.")
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
                     print(f"Error! There is not enough space to move any more files to the directory {file_dir}. ")
                     print(f"Total size of files in {manifest}.json (up to this point): {total_size}.\nFree space available on disk: {dir_size}.")
                     time.sleep(5)
                     mv_file = questionary.select(
                               f"Please select an option: \nA.) Move all files before {key} \nB.) Specify a new directory to move files to\nC.)Exit the program",
                               choices=["A", "B", "C"]
                                ).ask()
                     if mv_file == "A":
                        arr.pop(key)
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
        print(f"Please wait while the program moves the files over to the directory {file_dir}")
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
               print(f"This file {value} does not exist on the disk. Aborting move")
               logging.warning(f"This file {value} does not exist on the disk. Aborting move")
               failed_arr.append(value)        
     except Exception as e:
        print(f"Exception: {e}")
     logging.info(f"Successfully moved {move_count} entries to directory {file_dir}.")
     return  