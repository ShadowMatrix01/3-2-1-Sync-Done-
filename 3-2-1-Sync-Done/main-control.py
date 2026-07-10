#!/usr/bin/env python3 
import argparse #Needed for cmd to ensure user is given choice
#between full and partial backup.
import os
from datetime import datetime
from hashHOT import hash256_caller
from json_control import json_writer
from json_control import hash_compare
BATCH_SIZE = 2048 #Constant, because the amount of IO operations was slowing down the project by a lot.
buffer_arr = {}
write_now = False
def manifest_updater(file_path, hash_calc, write_now):
    global buffer_arr #Global because buffer_arr needs to be accessed globally.
    EXCLUDED = ["manifest.json", "loginfo.log"]
    if (file_path and hash_calc) and os.path.basename(file_path) not in EXCLUDED:
         buffer_arr[file_path] = {
                     "hash": hash_calc,
                     "last_seen": datetime.now().isoformat()
         }
    if ((len(buffer_arr) % BATCH_SIZE == 0) or write_now) and buffer_arr: #Prevents edge case that was happening during testing.
        print(f"Length of arr: {len(buffer_arr)}")
        json_writer(buffer_arr,"manifest.json")
def argCV():
    #Command Line Interface CLI, similar to C which makes sense.
    #considering python is an interpreted language.
    arg = argparse.ArgumentParser(description="3-2-1 Sync Done! A Data Integrity Solution")
    arg.add_argument("--path", required=True, help="Please add root directory.")
    arg.add_argument("--ext", help="Optional: Only backup files by extension (e.g., .jpg, .pdf, etc.)")
    return arg.parse_args()
argv = argCV()
for root, dirs, files in os.walk(argv.path):
    for file in files:
        if argv.ext and not file.endswith(argv.ext):
           continue
        if os.path.basename(file) in ["manifest.json", "loginfo.log"]:
           continue
        file_path = os.path.join(root, file)
        hash_calc = hash256_caller(file_path)
        if hash_calc:
           status = hash_compare(file_path, hash_calc, "manifest.json")
           if "new" in status: 
                manifest_updater(file_path, hash_calc, write_now=False)
           elif "corrupted" in status: 
                 print(f"WARNING! This file {file} has been changed or corrupted!")
                 sel = input("Type 'CONTINUE' to update manifest with new hash, or 'EXIT' to abort: ").strip().upper()
                 if sel == "CONTINUE":
                    manifest_updater(file_path, hash_calc, write_now=False)
                    print("Manifest has been updated, continuing program operation.")
                 elif sel == "EXIT":
                    manifest_updater(file_path, hash_calc, write_now=True)
                    print("Program quitting for data integrity purposes. Please check manifest.json and loginfo.log")
                    exit()
                 else:
                    manifest_updater(file_path, hash_calc, write_now=True)
                    print("Aborting program for security reasons.")
                    exit() 
           elif "same" in status:
                manifest_updater(file_path, hash_calc, write_now=False)
        else:
          print(f"FAILURE: The following {file} could not be hashed. Check loginfo.log for information.")  
manifest_updater(None, None, write_now=True)
#os.walk(): https://www.w3schools.com/python/ref_os_walk.asp
#shebang: https://realpython.com/python-shebang/ 
