import argparse #Needed for cmd to ensure user is given choice
#between full and partial backup.
import os
from hashHOT import hash256_caller
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
        file_path = os.path.join(root, file)
        hash_calc = hash256_caller(file_path)
        if hash_calc:
           print(f"SUCCESS: The file {file} was hashed as {hash_calc}.")
        else:
          print(f"FAILURE: The following {file} could not be hashed. Check loginfo.log for information.")  
        

#os.walk(): https://www.w3schools.com/python/ref_os_walk.asp
