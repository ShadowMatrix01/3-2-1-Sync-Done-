import os
import logging
from dotenv import load_dotenv
import requests
import json
import chime
import shutil #Added so the user can copy files from one location to another. 
import time
from datetime import datetime
from plyer import notification #now synchronous with plyer.
from discord_webhook import DiscordWebhook,  DiscordEmbed
from urllib.parse import urlparse 
logging.basicConfig(level=logging.WARNING, filename='VT_check.log', format='%(asctime)s - %(levelname)s: %(message)s')
load_dotenv()
def alert_sound():
    chime.theme('chime') 
    chime.info()
    return
def virus_local(file, count):
     try:
        notification.notify(
                title="CRITICAL: MALICIOUS FILE, ACTION NEEDED!",
                message=f"FILE: {file} MARKED AS MALICIOUS BY {count} VENDORS.",
                app_name="3-2-1-Sync-Done!",
                timeout=5
        )
        alert_sound()
     except Exception:
        pass    
def virus_webhook(file, count):
    webhook_id = os.getenv("WEBHOOK")
    if webhook_id is None:
       return
    url = urlparse(webhook_id)
    if not url.scheme or not url.netloc:
       return
    try:
        webhook = DiscordWebhook(url=webhook_id, rate_limit_retry=True)
        msg = DiscordEmbed(title="3-2-1-Sync-Done!", description=f"CRITICAL: {file} IS MARKED MALICIOUS BY {count} VENDORS. IMMEDIATE ACTION IS NEEDED NOW!", color="FF0000")
        webhook.add_embed(msg)
        response = webhook.execute()
        if response and response.status_code in (200, 204):
            return
        else:
            return
    except Exception:
        return   
def suspicious_file_log(file, response, dest):
   os.makedirs(dest, exist_ok=True)
   file_name = os.path.basename(file)
   log = os.path.join(dest, f"{file_name}_report.log")     
   with open(log, "w", encoding="utf-8") as f:
        time = datetime.now().isoformat()
        f.write(f"{file} was marked as suspicious on {time}. \nResponse from VT: {response}") 
        json.dump(response, f, indent=4)
def online_check(hash, file, pbar, local_notif, webhook_notif, version):
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
        rate_count = 0
        while True:
            response = requests.get(full_url, headers=headers)
            if response.status_code == 429 and rate_count < 4:
                for i in reversed(range(21)):
                    pbar.write(f"Attempt {rate_count + 1}/4: Rate limit reached. Please wait {i} seconds")
                    time.sleep(1)
                rate_count = rate_count + 1
                continue
            else:
                break
        if rate_count == 4:
            return "rate"  
        if response.status_code == 404:
           pbar.write(f"This file/blob {file} has not been seen on the VirusTotal database. Continuing program operation...")
           return "likely_safe"
        response.raise_for_status() #https://stackoverflow.com/questions/61463224/when-to-use-raise-for-status-vs-status-code-testing
        malicious(response.json(), file, pbar, local_notif, webhook_notif, version)
    except requests.exceptions.RequestException as e:
        pbar.write(f"API Error: {e}")
def malicious(response_info, file, pbar, local_notif, webhook_notif, vers):
    if isinstance(response_info, str): #If string, then it is an error code.
       pbar.write(f"An error was encountered: {response_info}")
       logging.basicConfig(level=logging.WARNING, filename='VT_check.log', format='%(asctime)s - %(levelname)s: %(message)s', force=True)
       logging.error(f"An error was encountered: {response_info}")
       return "error"
    info = response_info.get("data",{}).get("attributes", {}).get("last_analysis_stats",{})
    count = info.get("malicious", 0)
    if count > 5:
       if local_notif:
          virus_local(file, count)
       if webhook_notif:
          virus_webhook(file, count)
       if vers == "local":
          quarantine_file(file, count, response_info, pbar)
       elif vers == "online":
          quarantine_file_cloud(file, count, response_info, pbar)
def quarantine_file(suspicious_file, count, resp, pbar):
    quarantine_dir = "quarantine"
    os.makedirs(quarantine_dir, exist_ok=True)
    f = os.path.basename(suspicious_file)
    dst = os.path.join(quarantine_dir, f)
    logging.critical(f"ALERT! The file {suspicious_file} has been flagged by {count} vendors as being suspicious.")
    pbar.write(f"ALERT!: This file {suspicious_file} is flagged as malicious by {count} vendors.")
    while True:
        move = input("Enter 'Y' to move to quarantine folder, or 'N' if you believe this is a mistake: ").strip().upper()
        if move == "Y":
            try:
                #going to create specialized log with the vendors, and why it was flagged.
                #Includes file name, date, expected hash, actual hash, and response from vt.
                suspicious_file_log(suspicious_file, resp, dst)
                shutil.move(suspicious_file, dst)
                pbar.write("File has succesfully been moved to quarantine.")
                return "handled"
            except PermissionError:
                pbar.write("FAILURE: Program lacks permissions to move this file to quarantine. Aborting move.")
                continue
            except shutil.Error as e:
                pbar.write(f"ERROR: {e}")
                continue
            except OSError as e: 
                pbar.write(f"ERROR: {e}")
                continue
        elif move == "N":
            pbar.write("File remains in place, no further action taken. Continuing program operation...")
            return "likely_safe"
        else:
            pbar.write("Invalid input, please try again.")
            continue
def quarantine_file_cloud(blob, count, resp, pbar):
    return "handled"