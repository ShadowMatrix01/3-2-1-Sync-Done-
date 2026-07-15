#!/usr/bin/env python3 
import argparse #Needed for cmd to ensure user is given choice
#between full and partial backup.
import os
from datetime import datetime
from hashHOT import hash256_caller
from json_control import json_writer, hash_compare, load_manifest
from tqdm import tqdm
BATCH_SIZE = 4096 #Constant, because the amount of IO operations was slowing down the project by a lot.
buffer_arr = {}
write_now = False
EXCLUDED = ["manifest.json", "loginfo.log", "manifest2.json"]
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
    for file in files:
        if argv.ext and not file.endswith(argv.ext):
           continue
        if os.path.basename(file) in EXCLUDED:
           continue
        file_path = os.path.join(root, file)
        hash_calc = hash256_caller(file_path)
        if hash_calc:
           status = hash_compare(file_path, hash_calc, manifest_data)
           if "new" in status: 
                manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
           elif "corrupted" in status: 
                 pbar.write(f"\nWARNING! This file {file} has been changed or corrupted!")
                 sel = input("Type 'CONTINUE' to update manifest with new hash, or 'EXIT' to abort: ").strip().upper()
                 if sel == "CONTINUE":
                    manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
                    pbar.write("\nManifest has been updated, continuing program operation.")
                 elif sel == "EXIT":
                    pbar.write("\nProgram quitting for data integrity purposes. Please check manifest.json and loginfo.log")
                    exit()
                 else:
                    pbar.write("\nAborting program for security reasons.")
                    exit() 
           elif "same" in status:
                manifest_updater(file_path, hash_calc, write_now=False, which_one=this_one)
        else:
          pbar.write(f"FAILURE: The following file {file} could not be hashed. Check loginfo.log for information.")  
        pbar.update(1)
def manifest_updater(file_path, hash_calc, write_now, which_one):
    global buffer_arr #Global because buffer_arr needs to be accessed globally.
    if (file_path and hash_calc) and os.path.basename(file_path) not in EXCLUDED:
         buffer_arr[file_path] = {
                     "hash": hash_calc,
                     "last_seen": datetime.now().isoformat()
         }
    if ((len(buffer_arr) % BATCH_SIZE == 0) or write_now) and buffer_arr: #Prevents edge case that was happening during testing.
        if which_one == "source":
           json_writer(buffer_arr,"manifest.json")
        else:
           json_writer(buffer_arr,"manifest2.json")  
def argCV():
    #Command Line Interface CLI, similar to C which makes sense.
    #considering python is an interpreted language.
    arg = argparse.ArgumentParser(description="3-2-1 Sync Done! A Data Integrity Solution")
    arg.add_argument("--source", required=True, help="Please add root directory.")
    arg.add_argument("--source2", required=False, help="Optional: Add second directory to compare.")
    arg.add_argument("--ext", help="Optional: Only backup files by extension (e.g., .jpg, .pdf, etc.)")
    return arg.parse_args()
argv = argCV()
print("Please wait while the program discovers the total size of the directory(s)")
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
#os.walk(): https://www.w3schools.com/python/ref_os_walk.asp
#shebang: https://realpython.com/python-shebang/ 
#Progress barhttps://tqdm.github.io/