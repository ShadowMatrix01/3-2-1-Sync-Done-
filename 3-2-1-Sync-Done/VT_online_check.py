import os
import logging
from dotenv import load_dotenv
import requests
import shutil #Added so the user can copy files from one location to another. 
logging.basicConfig(level=logging.WARNING, filename='VT_check.log', format='%(asctime)s - %(levelname)s: %(message)s')
load_dotenv()
def online_check(hash, file):
    base_url = os.getenv("URL")
    api_key = os.getenv("APIKEY")
    if not api_key:
        print("Error: APIKEY not found. Please create a .env file based on .env.example")
        exit(1)
    if not base_url:
        print("Error: URL not found. Please create a .env file based on .env.example")
        exit(1) 
    full_url = f"{base_url}{hash}"
    headers = {"accept": "application/json", #VT's docs says this is the way, which is different.
                "x-apikey": api_key}
    try:
        response = requests.get(full_url, headers=headers)
        if response.status_code == 429:
            print("Rate limit reached. Please wait a moment.")
            return
        response.raise_for_status() #https://stackoverflow.com/questions/61463224/when-to-use-raise-for-status-vs-status-code-testing
        malicious(response.json(), file)
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
def malicious(response_info, file):
    if isinstance(response_info, str): #If string, then it is an error code.
       print(f"An error was encountered: {response_info}")
       return
    info = response_info.get("data",{}).get("attributes", {}).get("last_analysis_stats",{})
    count = info.get("malicious", 0)
    if count > 5:
       quarantine_file(file, count)
def quarantine_file(suspicious_file, count):
    logging.critical(f"ALERT! The file {suspicious_file} has been flagged by {count} vendors as being suspicious.")
    print(f"WARNING: This file {suspicious_file} is flagged as malicious by {count} vendors.")
    while True:
        move = input("Enter 'Y' to move to quarantine, or 'N' to keep it: ").strip().upper()
        if move == "Y":
            print("File has succesfully been moved to quarantine.")
            break
        elif move == "N":
            print("File remains in place, no further action.")
            break
        else:
            print("Invalid input, please try again.")
            continue
online_check("178ba564b39bd07577e974a9b677dfd86ffa1f1d0299dfd958eb883c5ef6c3e1", "C:\\Users\\test\\malware.txt") #Known malware hash, to check it works.