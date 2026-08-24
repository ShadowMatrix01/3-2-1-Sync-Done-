import os
from dotenv import load_dotenv
import requests
import time
import json
import chime
import logging
import re
import questionary
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
from plyer import notification #now synchronous with plyer.
from urllib.parse import urlparse 
from pathlib import Path
from dotenv import set_key
from timezones import timezones_from_file
def alert_sound():
    chime.theme('chime') 
    chime.info()
    return
app_state = {
    "local_notif": False,
    "webhook_notif": False,
    "vt_check": False
}
load_dotenv()
def main_menu(program):
    global app_state
    app_state = {
        "local_notif": True,
        "webhook_notif": True,
        "vt_check": True
    }
    while True:
        print("\nWelcome to the setup verification menu. \nFrom here, you can check if all services" 
        " such as Desktop Notifications are working the way you intend them to.")
        sel = questionary.select(
              "\nPlease select from the following options: \nA.)Desktop Notifications Check\nB.)Discord Webhook Integration Check\nC.)VirusTotal API Check\nD.)Set Alert Preferences\nE.)Azure Blob Storage Check\nF.)Set Auto-Schedule Preferences\nG.)Set Time and Timezone for Schedule\nH.)Exit the Menu\n",
              choices=["A", "B", "C", "D", "E", "F", "G", "H"]
              ).ask()
        if sel == "A":
           local_notification_check(program)
           break
        elif sel  == "B":
           webhook_check(program)
           break
        elif sel  == "C":
           vt_check(program)
           break
        elif sel == "D":
           alert_preferences(program)
           break
        elif sel == "E":
           azure_verify()
           break
        elif sel == "F":
           schedule_preferences(program)
           break
        elif sel == "G":
           schedule_time()
           break
        elif sel == "H":
           exit()
        else:
           print("Invalid input. Please try again.")
           continue
def rebuild(program, vers):
    if program == "main-control":
       value = "true"
    else:
       value = "false"
    data = {
                "webhook_alerts":"false",
                "local_alerts":"false",
                "virus_total_check":"false",
                "first_run": value
    }
    data_2 = {
                "virus_check": "manual",
                "quarantine": "manual"
    }
    if vers == "alert":
        with open("alert_api_preferences.json", "w") as f:
            json.dump(data, f, indent=4)
    else:
        with open("schedule_pref.json", "w") as f:
             json.dump(data_2, f, indent=4)
def fmt(inp):
    pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
    #This pattern is so that my program auto-rejects invalid time.
    m = re.match(pattern, inp)
    # noinspection redundant-parentheses
    return (m is not None)
    #https://stackoverflow.com/questions/50224919/best-way-to-ensure-that-user-input-confirms-with-specific-format-in-python
def schedule_time():
    try:
        while True:
            env_file = Path(".env")
            load_dotenv(env_file, override=True)
            time_sch = os.getenv("TIME_IN_24_HOURS")
            timezone = os.getenv("TIMEZONE_DST_AWARE")
            # noinspection string-conversion-without-dunder-method
            print(f"\nPrinting Current Settings: \nTime: {time_sch} \nTimezone: {timezone}")
            sel = questionary.select(
                  "What value would you like to modify?\nA.)Time\nB.)Timezone\nC.)None, Exit\n",
                  choices=["A", "B", "C"]
                ).ask()
            if sel == "A":
               while True:
                    sel_2 = questionary.text("Please enter a time (24 Hours) in the format HH:MM. Example: 03:30\n").ask()
                    result = fmt(sel_2)
                    if not result:
                        print("Error! Invalid input, please try again!")
                        continue
                    else:
                        print(f"Success! Time has now been set to {sel_2}.")
                        set_key(dotenv_path=env_file, key_to_set="TIME_IN_24_HOURS", value_to_set=sel_2)
                        break
            elif sel == "B":
                select = questionary.select(
                    "Please select a timezone:",
                    choices=timezones_from_file()
                ).ask()
                print(f"Success! Timezone has now been set to {select}.")
                set_key(dotenv_path=env_file, key_to_set="TIMEZONE_DST_AWARE", value_to_set=select)
                continue
               #https://github.com/tmbo/questionary
            elif sel  == "C":
                exit()
            else:
                print("\nInvalid input, please try again!")
                continue
        #https://saurabh-kumar.com/python-dotenv/reference/
    except Exception as e:
        print(f"Exception: {e}")
        exit()
def alert_preferences(program):
    global app_state
    keys = {"webhook_alerts", "local_alerts", "virus_total_check", "first_run"}
    values = {"false", "true"}
    try:
        with open("alert_api_preferences.json", "r") as f:
            info = json.load(f)
        check_key = keys.issubset(info.keys())
        check_values = check_key and all(info.get(val) in values for val in keys)
        if not check_values:
            print("Missing or invalid values, deleting file and rebuilding.")
            os.remove("alert_api_preferences.json")
            rebuild(program, "alert")
            if program == "main-control":
                return False 
        else:
            #Had to do this, since booleans do not persist across multiple calls.
            app_state["local_notif"] = (info.get("local_alerts") == "true")
            app_state["webhook_notif"] = (info.get("webhook_alerts") == "true")
            app_state["vt_check"] = (info.get("virus_total_check") == "true")
            if program == "notify":
                print("\nPreferences file validated, printing current settings.")
                for key in keys:
                    print(f"{key}: {info[key]}")
                while True: 
                    sel = questionary.select(
                          "\nWhat values would you like to modify?"
                          "\nA.)Webhook Alerts\nB.)Local Notifications\nC.)VirusTotal API Check\nD.)Disable all features\nE.)Enable all features\nF.)None, Exit\n",
                          choices=["A", "B", "C", "D", "E", "F"]
                          ).ask()
                    if sel == "A":
                        info["webhook_alerts"] = "false" if info.get("webhook_alerts") == "true" else "true"
                    elif sel == "B":
                        info["local_alerts"] = "false" if info.get("local_alerts") == "true" else "true"
                    elif sel == "C":
                        info["virus_total_check"] = "false" if info.get("virus_total_check") == "true" else "true"
                    elif sel == "D":
                        info["webhook_alerts"] = "false"
                        info["virus_total_check"] = "false"
                        info["local_alerts"] = "false"
                    elif sel == "E":
                        info["webhook_alerts"] = "true"
                        info["virus_total_check"] = "true"
                        info["local_alerts"] = "true"
                    elif sel == "F":
                        break       
                    else: 
                        print("\nInvalid input, please try again.")
                        continue 
                    info["first_run"] = "false"    
                    with open("alert_api_preferences.json", "w") as f:
                        json.dump(info, f, indent=4)
                        print("\nPreferences updated successfully!\nNew Preferences:")
                        for key in keys:
                            print(f"{key}: {info[key]}")
                        break
            else:
                if info["first_run"] == "false":
                    return True
                else:    
                    return False   
    except FileNotFoundError:
        print("\nRebuilding alert_api_preferences.json")
        rebuild(program, "alert")
        if program == "main-control":
            return False 
    except json.JSONDecodeError:
        print("\nInvalid json, rebuilding from scratch")
        os.remove("alert_api_preferences.json")
        rebuild(program, "alert")
        if program == "main-control":
            return False  
def schedule_preferences(program):
    keys = {"virus_check", "quarantine"}
    values = {"false", "manual", "true"}
    try:
        with open("schedule_pref.json", "r") as f:
            info = json.load(f)
        check_key = keys.issubset(info.keys())
        check_values = check_key and all(info.get(val) in values for val in keys)
        if not check_values:
            print("Missing or invalid values, deleting file and rebuilding.")
            os.remove("schedule_pref.json")
            rebuild(program, "schedule")
            if program == "main-control":
                return False 
        else:
                print("\nPreferences file validated, printing current settings.")
                for key in keys:
                    print(f"{key}: {info[key]}")
                if program == "main-control":
                   return True
                while True: 
                    sel = questionary.select(
                        "\nWhat values would you like to modify?"
                         "\nA.)Quarantine Preferences\nB.)VirusTotal Check Preferences\nC.)Disable Quarantining and VirusTotal Check\nD.)Enable Quarantining and VirusTotal Check\nE.)Make Quarantining and VirusTotal Check Manual\nF.)None, Exit\n",
                          choices=["A", "B", "C", "D", "E", "F"]
                    ).ask()                   
                    if sel == "A":
                       while True:
                           print("\nPlease select from the following options:")
                           sel_2 = questionary.select(
                                   "\nPlease select from the following options:",
                                   "\nA.)Auto-Quarantine\nB.)Disable Quarantining\nC.)Manually Decide to Quarantine\nD.)None, Exit\n",
                                   choices=["A", "B", "C", "D"]
                           ).ask()   
                           match sel_2:
                               case "A":
                                   info["quarantine"] = "true"  
                                   print("\nAuto-Quarantine Enabled")
                                   break  
                               case "B":
                                   info["quarantine"] = "false"
                                   print("\nAuto-Quarantine Disabled")
                                   break
                               case "C":
                                   info["quarantine"] = "manual"
                                   print("\nManual Quarantining Enabled")
                                   break
                               case "D":
                                   break
                               case _:
                                   print("\nInvalid input, please try again")   
                                   continue 
                    elif sel == "B":
                       while True:
                           sel_2 = questionary.select(
                                   "\nPlease select from the following options:",
                                   "\nA.)Auto-Check with VirusTotal\nB.)Disable Checking with VirusTotal\nC.)Manually Decide to Check with VirusTotal\nD.)None, Exit\n",
                                   choices=["A", "B", "C", "D"]
                           ).ask()   
                           match sel_2:
                               case "A":
                                   info["virus_check"] = "true"
                                   break    
                               case "B":
                                   info["virus_check"] = "false"
                                   break
                               case "C":
                                   info["virus_check"] = "manual"
                                   break
                               case "D":
                                   break
                               case _:
                                   print("\nInvalid input, please try again")   
                                   continue                          
                    elif sel == "C":
                        info["virus_check"] = "false"
                        info["quarantine"] = "false"
                    elif sel == "D":
                        info["virus_check"] = "true"
                        info["quarantine"] = "true"
                    elif sel == "E":
                        info["virus_check"] = "manual"
                        info["quarantine"] = "manual"  
                    elif sel == "F":
                        break       
                    else: 
                        print("\nInvalid input, please try again.")
                        continue 
                    with open("schedule_pref.json", "w") as f:
                        json.dump(info, f, indent=4)
                        print("\nPreferences updated successfully!\nNew Preferences:")
                        for key in keys:
                            print(f"{key}: {info[key]}")
                        break
    except FileNotFoundError:
        print("\nRebuilding schedule_pref.json")
        rebuild(program, "schedule")
        if program == "main-control":
            return False 
    except json.JSONDecodeError:
        print("\nInvalid json, rebuilding from scratch")
        os.remove("schedule_pref.json")
        rebuild(program, "schedule")
        if program == "main-control":
            return False 
def azure_verify():
    logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
    azure_connection_string = os.getenv("AZURE_CONNECT_STR")
    azure_container_name = os.getenv("AZURE_CONTAINER")
    azure_container_name_2 = os.getenv("AZURE_CONTAINER_QUARANTINE")
    if not azure_connection_string:
       print("Error: AZURE_CONNECT_STR not found. Please create a .env file based on .env example")
       return
    if not azure_container_name:
       print("Error: AZURE_CONTAINER not found. Please create a .env file based on .env example")
       return
    if not azure_container_name_2:
       print("Error: AZURE_CONTAINER_QUARANTINE not found. Please create a .env file based on .env example")
       return
    try:
       blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
       print("Connection to Azure Blob Storage was successful...")
       container_client = blob_service_client.get_container_client(container=azure_container_name)
       if not container_client.exists():
          print(f"Connection to source container {azure_container_name} was not successful.")
          return
       else:
          print(f"Connection to source container {azure_container_name} was successful.")
       container_client_2 = blob_service_client.get_container_client(container=azure_container_name_2)
       if not container_client_2.exists():
          print(f"Connection to quarantine container {azure_container_name_2} was not successful.")
          return
       else:
         print(f"Connection to quarantine container {azure_container_name_2} was successful.")
    except HttpResponseError as e:
        print(f"Azure Container Error: {e.status_code}: {e.message}")
        logging.error(f"Azure Container Error: {e.status_code}: {e}")
    except Exception as e:
        print(f"Unexpected Azure Error: {e}")
        logging.error(f"Unexpected Azure Error: {e}")
def local_notification_check(program): 
    #This function is now synchronous, WINRT will always complain regardless of what I attempt with async,
    #making the program look like an error has happened when it hasn't. Even suppressing the warning does not work since that
    #is deprecated, as such this has been modified accordingly. It now uses the plyer notifications library, which is
    #also cross-platform.
    if program == "main-control" and not app_state["local_notif"]:
        print("Desktop notifications are disabled.")  
        time.sleep(2)
        return False 
    try:
        notification.notify(
            title="3-2-1-Sync-Done!",
            message="A Data Integrity Solution.",
            app_name="3-2-1-Sync-Done!",
            timeout=5
        )
        alert_sound()
    except Exception:
        pass             
    print("\nIf a message did not appear on your screen, it is likely notifications are disabled. \nPlease enable them or visit: https://pypi.org/project/plyer/")
    # noinspection inconsistent-returns
    if program == "main-control":
        return True
def webhook_check(program):
    if program == "main-control" and not app_state["webhook_notif"]:
        print("Webhook alerts are disabled.")  
        time.sleep(2)
        return False 
    webhook_id = os.getenv("WEBHOOK")
    if webhook_id is None:
       print("Error: WEBHOOK not found. Please create a .env file based on .env.example")
       if program == "main-control":
          print("Webhook alerts are disabled.")  
          time.sleep(2)
          return False
       # noinspection inconsistent-returns
       return
    url = urlparse(webhook_id)
    if not url.scheme or not url.netloc:
       print("Invalid webhook URL format, please check .env.")
       if program == "main-control":
          print("Webhook alerts are disabled.")  
          time.sleep(2)
          return False
       # noinspection inconsistent-returns
       return
    try:
        response = requests.get(webhook_id, timeout=5) #Modified because in testing the program
        #I realized it would be annoying to constantly receive message that it is working, instead of critical messages.
        if response and response.status_code in (200, 204):
            print("Webhook was successful!")
            if program == "main-control":
               return True
            # noinspection inconsistent-returns
            return
        else:
            print("Invalid webhook or connection error, please check .env.")
            if program == "main-control":
               print("Webhook alerts are disabled.")  
               time.sleep(2)
               return False
            # noinspection inconsistent-returns
            return
    except Exception:
        print(f"Invalid webhook or connection error, please check .env and loginfo.log.")
        if program == "main-control":
           print("Webhook alerts are disabled.")  
           time.sleep(2)
           return False
        # noinspection inconsistent-returns
        return
def vt_check(program):
       if program == "main-control" and not app_state["vt_check"]:
           print("Checking the hash with VirusTotal API is disabled.")  
           time.sleep(2)
           return False 
       print("Please wait while the program connects to the VirusTotal API.")
       time.sleep(2)
       hash_in = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f" #A SHA-256 hash of a known safe virus.
       base_url = os.getenv("URL")
       api_key = os.getenv("APIKEY")
       # noinspection bad-argument-type
       url = urlparse(base_url)
       if not api_key:
           if program == "notify":
              print("Error: APIKEY not found. Please create a .env file based on .env.example")
              exit()
           elif program == "main-control":
              print("Error: APIKEY not found. Please create a .env file based on .env.example")
              print("The program will run in 5 seconds, but checking the hash with VirusTotal API will be disabled.")  
              time.sleep(2)
              return False
       if not base_url or not url.scheme or not url.netloc:
           if program == "notify":
              print("Error: URL not found. Please create a .env file based on .env.example")
              exit() 
           elif program == "main-control":
              print("Error: URL not found. Please create a .env file based on .env.example") 
              print("The program will run in 5 seconds, but checking the hash with VirusTotal API will be disabled.")  
              time.sleep(2)
              return False
       # noinspection string-conversion-without-dunder-method
       full_url = f"{base_url}{hash_in}"
       headers = {"accept": "application/json", 
                   "x-apikey": api_key}
       try:
           response = requests.get(full_url, headers=headers)
           if response.status_code == 429:
               if program == "notify":
                    print("Rate limit reached. Please wait a moment.")
                    # noinspection inconsistent-returns
                    return
               elif program == "main-control":
                    print("Rate limit reached. Please wait a couple of seconds.")
                    time.sleep(5)
                    return True
           elif response.status_code == 401:
               if program == "notify":
                    print("Authentication Error: Invalid API key.")
                    # noinspection inconsistent-returns
                    return
               elif program == "main-control":
                    print("Authentication Error: Invalid API key.")
                    print("The program will run in 5 seconds, but checking the hash with VirusTotal API will be disabled.")  
                    time.sleep(2)
                    return False
           elif response.status_code == 404:
               if program == "notify":
                    print("Connection to VirusTotal API was not successful.")
                    # noinspection inconsistent-returns
                    return
               elif program == "main-control":
                    print("Connection to VirusTotal API was not successful.")
                    print("The program will run in 5 seconds, but checking the hash with VirusTotal API will be disabled.")  
                    time.sleep(2)
                    return False
           if program == "main-control":
              print("The program successfully connected to the VirusTotal API.")
              time.sleep(2)
              return True
           response.raise_for_status() #https://stackoverflow.com/questions/61463224/when-to-use-raise-for-status-vs-status-code-testing
           data = response.json()
           attributes = data.get("data", {}).get("attributes", {})
           # noinspection SpellCheckingInspection
           name = attributes.get("meaningful_name") or attributes.get("tfph_sha256") or "Unknown"
           stats = attributes.get("last_analysis_stats", {})
           malicious_count = stats.get("malicious", 0)
           status = "Yes, Malicious" if malicious_count > 5 else "No, Clean"
           print(f"Name: {name}")
           print(f"Name: {hash_in}")
           print(f"Is this malicious: {status} by ({malicious_count} detections)")
       except requests.exceptions.RequestException as e:
           print(f"API Error: {e}")
           if program == "main-control":
              print("Checking the hash with VirusTotal API is disabled.")  
              time.sleep(2)
              return False 
#https://pypi.org/project/discord-webhook/
#https://pypi.org/project/plyer/
#https://pypi.org/project/chime/