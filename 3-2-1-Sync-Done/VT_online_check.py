import os
import logging
from dotenv import load_dotenv
import requests
import json
import chime
import shutil #Added so the user can copy files from one location to another. 
import time
from datetime import datetime
from azure.core.exceptions import HttpResponseError
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
                title="CRITICAL: MALICIOUS FILE/BLOB, ACTION NEEDED!",
                message=f"FILE/BLOB: {file} MARKED AS MALICIOUS BY {count} VENDORS.",
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
        msg = DiscordEmbed(title="3-2-1-Sync-Done!", description=f"CRITICAL: FILE/BLOB: {file} IS MARKED MALICIOUS BY {count} VENDORS. IMMEDIATE ACTION IS NEEDED NOW!", color="FF0000")
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
def suspicious_blob_log(blob, response, dest, source):
    os.makedirs(dest, exist_ok=True)
    log = os.path.join(dest, f"{blob}_report.log")     
    with open(log, "w", encoding="utf-8") as f:
         time = datetime.now().isoformat()
         f.write(f"{blob} was marked as suspicious on {time}. \nResponse from VT: {response}") 
         json.dump(response, f, indent=4)  
    with open(file=log, mode="rb") as stream:
         blob_client = source.upload_blob(name=f"{blob}_report.log", data=stream, overwrite=True)
def online_check(hash, file, pbar, local_notif, webhook_notif, version, client):
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
        malicious(response.json(), file, pbar, local_notif, webhook_notif, version, client)
    except requests.exceptions.RequestException as e:
        pbar.write(f"API Error: {e}")
def malicious(response_info, file, pbar, local_notif, webhook_notif, vers, blob_client):
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
          quarantine_file_cloud(file, count, response_info, pbar, blob_client)
def quarantine_file(suspicious_file, count, resp, pbar):
    quarantine_dir = "quarantine"
    os.makedirs(quarantine_dir, exist_ok=True)
    f = os.path.basename(suspicious_file)
    dst = os.path.join(quarantine_dir, f)
    logging.critical(f"ALERT! The file {suspicious_file} has been flagged by {count} vendors as being suspicious.")
    pbar.write(f"ALERT!: This file {suspicious_file} is flagged as malicious by {count} vendors.")
    while True:
        pbar.write("Enter 'Y' to move to quarantine folder, or 'N' if you believe this is a mistake: ")
        move = input(" ").strip().upper()
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
                break
            except shutil.Error as e:
                pbar.write(f"ERROR: {e}")
                break
            except OSError as e: 
                pbar.write(f"ERROR: {e}")
                break
        elif move == "N":
            pbar.write("File remains in place, no further action taken. Continuing program operation...")
            return "likely_safe"
        else:
            pbar.write("Invalid input, please try again.")
            continue
def quarantine_file_cloud(blob, count, resp, pbar, client): 
    quarantine_dir = "quarantine_cloud"
    os.makedirs(quarantine_dir, exist_ok=True)
    dst = os.path.join(quarantine_dir, blob)
    logging.critical(f"ALERT! The blob {blob} has been flagged by {count} vendors as being suspicious.")
    pbar.write(f"ALERT!: This blob {blob} is flagged as malicious by {count} vendors.")
    logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
    while True:
        pbar.write("Enter 'Y' to move to quarantine container (cloud), or 'N' if you believe this is a mistake: ")
        move = input(" ").strip().upper()
        if move == "Y":
            try:
                status = quarantine_file_cloud_2(blob, pbar, client, resp, dst)
                return status
            except OSError as e: 
                pbar.write(f"ERROR: {e}")
                continue
            except Exception as e: 
                pbar.write(f"Unexpected Error: {e}")
                logging.error(f"Unexpected Error: {e}")
                return "unexpected_error"
        elif move == "N":
            pbar.write("Blob remains in place, no further action taken. Continuing program operation...")
            return "likely_safe"
        else:
            pbar.write("Invalid input, please try again.")
            continue
def quarantine_file_cloud_2(blob, pbar, client, resp, dst): 
    azure_container_name = os.getenv("AZURE_CONTAINER")
    azure_container_name_2 = os.getenv("AZURE_CONTAINER_QUARANTINE")
    if not azure_container_name:
        print("Error: AZURE_CONTAINER not found. Please create a .env file based on .env.example")
        return "error_azure"
    if not azure_container_name_2:
        print("Error: AZURE_CONTAINER_QUARANTINE for Quarantine not found. Please create a .env file based on .env.example")
        return "error_azure"
    try:
        source = client.get_blob_client(container=azure_container_name, blob=blob)
        source_2 = client.get_container_client(container=azure_container_name_2)
        quarantined_blob_name = f"QUARANTINED_{datetime.now()}_{blob}"
        target_blob = client.get_blob_client(container=azure_container_name_2, blob=quarantined_blob_name)
        target_blob.start_copy_from_url(source.url)
        suspicious_blob_log(blob, resp, dst, source_2)
        pbar.write(f"The suspicious blob {blob} was moved to the quarantine container.")
        pbar.write(f"The blob {blob} will now be soft deleted for security reasons.")
        source.delete_blob()
        pbar.write(f"The blob {blob} was soft deleted from the cloud.")
        return "handled"
    except HttpResponseError as e:
        pbar.write(f"Azure Container Error: {e.status_code}: {e.message}")
        logging.error(f"Azure Container Error: {e.status_code}: {e}")
        return "error_azure"
    except Exception as e:
        pbar.write(f"Unexpected Azure Error: {e}")
        logging.error(f"Unexpected Azure Error: {e}")
        return "error_azure"
    #https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-copy-async-python