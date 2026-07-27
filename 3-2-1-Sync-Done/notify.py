import os
from dotenv import load_dotenv
import requests
import time
import json
from plyer import notification #now synchronous with plyer.
from discord_webhook import DiscordWebhook,  DiscordEmbed
from urllib.parse import urlparse 
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
        print("\nWelcome to the setup verification menu. \nFrom here, you can check if all three external services" 
        " like Desktop Notifications, Discord Webhook Integration, and VirusTotal API are working, aswell as set preferences for webhook alerts.")
        sel = input("\nPlease select from the following options by typing the corresponding letter:\nA.Desktop Notifications Check\nB.Discord Webhook Integration\nC.VirusTotal API\nD.Set Alert Preferences\nE.Exit the Menu\n")
        if sel.strip().upper() == "A":
           local_notification_check(program)
           break
        elif sel.strip().upper()  == "B":
           webhook_check(program)
           break
        elif sel.strip().upper()  == "C":
           VT_check(program)
           break
        elif sel.strip().upper() == "D":
           alert_preferences(program)
           break
        elif sel.strip().upper() == "E":
           exit()
        else:
           print("Invalid input. Please try again.")
           continue
def rebuild(program):
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
    with open("alert_api_preferences.json", "w") as f:
         json.dump(data, f, indent=4)
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
            rebuild(program)
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
            else:
                return True   
    except FileNotFoundError:
        print("\nRebuilding alert_api_preferences.json")
        rebuild(program)
        if program == "main-control":
            return False 
    except json.JSONDecodeError:
        print("\nInvalid json, rebuilding from scratch")
        os.remove("alert_api_preferences.json")
        rebuild(program)
        if program == "main-control":
            return False 
    return 
def local_notification_check(program): 
    #This funtion is now syncrhonous, WINRT will always complain regardless of what I attempt with async, 
    #making the program look like an error has happened when it hasn't. Even supressing the warning does not work since that
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
    except Exception:
        pass             
    print("\nIf a message did not appear on your screen, it is likely notifications are disabled. \nPlease enable them or visit: https://pypi.org/project/desktop-notifier/ ")
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
       return
    url = urlparse(webhook_id)
    if not url.scheme or not url.netloc:
       print("Invalid webhook URL format, please check .env.")
       if program == "main-control":
          print("Webhook alerts are disabled.")  
          time.sleep(2)
          return False 
       return
    try:
        webhook = DiscordWebhook(url=webhook_id, rate_limit_retry=True)
        msg = DiscordEmbed(title="3-2-1-Sync-Done!", description="Webhook is functional! \nIn normal use, this would be red and have more information.", color="00FF00")
        webhook.add_embed(msg)
        response = webhook.execute()
        if response and response.status_code in (200, 204):
            print("Webhook was successful! Please check your Discord server.")
            if program == "main-control":
               return True
            return
        else:
            print("Invalid webhook or connection error, please check .env.")
            if program == "main-control":
               print("Webhook alerts are disabled.")  
               time.sleep(2)
               return False 
            return
    except Exception:
        print(f"Invalid webhook or connection error, please check .env and loginfo.log.")
        if program == "main-control":
           print("Webhook alerts are disabled.")  
           time.sleep(2)
           return False 
        return
def VT_check(program):
       if program == "main-control" and not app_state["vt_check"]:
           print("Checking the hash with VirusTotal API is disabled.")  
           time.sleep(2);
           return False 
       print("Please wait while the program connects to the VirusTotal API.")
       time.sleep(2)
       hash = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f" #A SHA-256 hash of a known safe virus.
       base_url = os.getenv("URL")
       api_key = os.getenv("APIKEY")
       if not api_key:
           if program == "notify":
              print("Error: APIKEY not found. Please create a .env file based on .env.example")
              exit()
           elif program == "main-control":
              print("Error: APIKEY not found. Please create a .env file based on .env.example")
              print("The program will run in 5 seconds, but checking the hash with VirusTotal API will be disabled.")  
              time.sleep(2);
              return False
       if not base_url:
           if program == "notify":
              print("Error: URL not found. Please create a .env file based on .env.example")
              exit() 
           elif program == "main-control":
              print("Error: URL not found. Please create a .env file based on .env.example") 
              print("The program will run in 5 seconds, but checking the hash with VirusTotal API will be disabled.")  
              time.sleep(2);
              return False
       full_url = f"{base_url}{hash}"
       headers = {"accept": "application/json", 
                   "x-apikey": api_key}
       try:
           response = requests.get(full_url, headers=headers)
           if response.status_code == 429:
               if program == "notify":
                    print("Rate limit reached. Please wait a moment.")
                    return
               elif program == "main-control":
                    print("Rate limit reached. Please wait a couple of seconds.")
                    time.sleep(5)
                    return True
           elif response.status_code == 401:
               if program == "notify":
                    print("Authentication Error: Invalid API key.")
                    return
               elif program == "main-control":
                    print("Authentication Error: Invalid API key.")
                    print("The program will run in 5 seconds, but checking the hash with VirusTotal API will be disabled.")  
                    time.sleep(2);
                    return False
           elif response.status_code == 404:
               if program == "notify":
                    print("Connection to VirusTotal API was not successful.")
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
           name = attributes.get("meaningful_name") or attributes.get("tfph_sha256") or "Unknown"
           stats = attributes.get("last_analysis_stats", {})
           malicious_count = stats.get("malicious", 0)
           status = "Yes, Malicious" if malicious_count > 5 else "No, Clean"
           print(f"Name: {name}")
           print(f"Name: {hash}")
           print(f"Is this malicious: {status} by ({malicious_count} detections)")
       except requests.exceptions.RequestException as e:
           print(f"API Error: {e}")
           if program == "main-control":
              print("Checking the hash with VirusTotal API is disabled.")  
              time.sleep(2);
              return False 
#https://pypi.org/project/discord-webhook/
#https://www.geeksforgeeks.org/python/python-desktop-notifier-using-plyer-module/
#https://pypi.org/project/plyer/