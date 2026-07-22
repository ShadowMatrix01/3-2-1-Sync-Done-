import os
import logging
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import shutil #Added so the user can copy files from one location to another. 
logging.basicConfig(level=logging.WARNING, filename='VT_check.log', format='%(asctime)s - %(levelname)s: %(message)s')
load_dotenv()
def suspicious_file_log(file, response, dest):
   os.makedirs(dest, exist_ok=True)
   file_name = os.path.basename(file)
   log = os.path.join(dest, f"{file_name}_report.log")     
   with open(log, "w", encoding="utf-8") as f:
        time = datetime.now().isoformat()
        f.write(f"{file} was marked as suspicious on {time}. \nResponse from VT: {response}") 
        json.dump(response, f, indent=4)
def online_check(hash, file, pbar):
    base_url = os.getenv("URL")
    api_key = os.getenv("APIKEY")
    if not api_key:
        pbar.write("Error: APIKEY not found. Please create a .env file based on .env.example")
        exit(1)
    if not base_url:
        pbar.write("Error: URL not found. Please create a .env file based on .env.example")
        exit(1) 
    full_url = f"{base_url}{hash}"
    headers = {"accept": "application/json", #VT's docs says this is the way, which is different.
                "x-apikey": api_key}
    try:
        response = requests.get(full_url, headers=headers)
        if response.status_code == 429:
            pbar.write("Rate limit reached. Please wait a moment.")
            return
        response.raise_for_status() #https://stackoverflow.com/questions/61463224/when-to-use-raise-for-status-vs-status-code-testing
        malicious(response.json(), file, pbar)
    except requests.exceptions.RequestException as e:
        pbar.write(f"API Error: {e}")
def malicious(response_info, file, pbar):
    if isinstance(response_info, str): #If string, then it is an error code.
       pbar.write(f"An error was encountered: {response_info}")
       return
    info = response_info.get("data",{}).get("attributes", {}).get("last_analysis_stats",{})
    count = info.get("malicious", 0)
    if count > 5:
       quarantine_file(file, count, response_info, pbar)
def quarantine_file(suspicious_file, count, resp, pbar):
    quarantine_dir = "quarantine"
    os.makedirs(quarantine_dir, exist_ok=True)
    f = os.path.basename(suspicious_file)
    dst = os.path.join(quarantine_dir, f)
    logging.critical(f"ALERT! The file {suspicious_file} has been flagged by {count} vendors as being suspicious.")
    pbar.write(f"WARNING: This file {suspicious_file} is flagged as malicious by {count} vendors.")
    while True:
        move = input("Enter 'Y' to move to quarantine folder, or 'N' if you believe this is a mistake: ").strip().upper()
        if move == "Y":
            try:
                #going to create specialized log with the vendors, and why it was flagged.
                #Includes file name, date, expected hash, actual hash, and response from vt.
                suspicious_file_log(suspicious_file, resp, dst)
                shutil.move(suspicious_file, dst)
                pbar.write("File has succesfully been moved to quarantine.")
                break
            except PermissionError:
                pbar.write("FAILURE: Program lacks permissions to move this file to quarantine. Aborting move.")
            except shutil.Error as e:
                pbar.write(f"ERROR: {e}")
            except OSError as e: 
                pbar.write(f"ERROR: {e}")
        elif move == "N":
            pbar.write("File remains in place, no further action taken.")
            break
        else:
            pbar.write("Invalid input, please try again.")
            continue
