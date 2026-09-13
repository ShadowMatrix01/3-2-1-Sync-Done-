import os
from dotenv import load_dotenv
import requests
import time
import json
import chime
import logging
import re
import questionary
import customtkinter as ctk
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
def main_menu(app, program):
    global app_state
    app_state = {
        "local_notif": True,
        "webhook_notif": True,
        "vt_check": True
    }
    while True:
        app.write_box("\nWelcome to the setup verification menu. \nFrom here, you can check if all services" 
        " such as Desktop Notifications are working the way you intend them to.")
        sel = questionary.select(
              "\nPlease select from the following options: \nA.)Desktop Notifications Check\nB.)Discord Webhook Integration Check\nC.)VirusTotal API Check\nD.)Set Alert Preferences\nE.)Azure Blob Storage Check\nF.)Set Auto-Schedule Preferences\nG.)Set Time and Timezone for Schedule\nH.)Exit the Menu\n",
              choices=["A", "B", "C", "D", "E", "F", "G", "H"]
              ).ask()
        if sel == "A":
           local_notification_check(app, program)
           break
        elif sel  == "B":
           webhook_check(app, program)
           break
        elif sel  == "C":
           vt_check(app, program)
           break
        elif sel == "D":
           alert_preferences(program)
           break
        elif sel == "E":
           azure_verify(app)
           break
        elif sel == "F":
           schedule_preferences(program)
           break
        elif sel == "G":
           schedule_time(app)
           break
        elif sel == "H":
           exit()
        else:
           app.write_box("Invalid input. Please try again.")
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
def schedule_time(app):
    try:
        while True:
            env_file = Path(".env")
            load_dotenv(env_file, override=True)
            time_sch = os.getenv("TIME_IN_24_HOURS_LOCAL")
            time_sch_2 = os.getenv("TIME_IN_24_HOURS_CLOUD")
            timezone = os.getenv("TIMEZONE_DST_AWARE")
            # noinspection string-conversion-without-dunder-method
            app.write_box(f"\nPrinting Current Settings: \nTime: {time_sch} \nTimezone: {timezone}")
            sel = questionary.select(
                  "What value would you like to modify?\nA.)Local Scheduler Time\nB.)Cloud Scheduler Time\nC.)Timezone\nD.)None, Exit\n",
                  choices=["A", "B", "C", "D"]
                ).ask()
            if sel == "A":
               while True:
                    sel_2 = questionary.text("Please enter a time (24 Hours) in the format HH:MM for local scheduler. Example: 03:30\n").ask()
                    result = fmt(sel_2)
                    if not result:
                        app.write_box("Error! Invalid input, please try again!")
                        continue
                    else:
                        app.write_box(f"Success! Time has now been set to {sel_2}.")
                        set_key(dotenv_path=env_file, key_to_set="TIME_IN_24_HOURS_LOCAL", value_to_set=sel_2)
                        break
            elif sel == "B":
               while True:
                    sel_3 = questionary.text("Please enter a time (24 Hours) in the format HH:MM for cloud scheduler. Example: 03:30\n").ask()
                    result = fmt(sel_3)
                    if not result:
                        app.write_box("Error! Invalid input, please try again!")
                        continue
                    else:
                        app.write_box(f"Success! Time has now been set to {sel_2}.")
                        set_key(dotenv_path=env_file, key_to_set="TIME_IN_24_HOURS_CLOUD", value_to_set=sel_3)
                        break
            elif sel == "C":
                select = questionary.select(
                    "Please select a timezone:",
                    choices=timezones_from_file()
                ).ask()
                app.write_box(f"Success! Timezone has now been set to {select}.")
                set_key(dotenv_path=env_file, key_to_set="TIMEZONE_DST_AWARE", value_to_set=select)
                continue
               #https://github.com/tmbo/questionary
            elif sel  == "D":
                exit()
            else:
                app.write_box("\nInvalid input, please try again!")
                continue
        #https://saurabh-kumar.com/python-dotenv/reference/
    except Exception as e:
        app.write_box(f"Exception: {e}")
        exit()
def alert_preferences(app, program):
    global app_state
    keys = {"webhook_alerts", "local_alerts", "virus_total_check", "first_run"}
    values = {"false", "true"}
    try:
        with open("alert_api_preferences.json", "r") as f:
            info = json.load(f)
        check_key = keys.issubset(info.keys())
        check_values = check_key and all(info.get(val) in values for val in keys)
        if not check_values:
            app.write_box("Missing or invalid values, deleting file and rebuilding.")
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
                app.write_box("\nPreferences file validated, printing current settings.")
                for key in keys:
                    app.write_box(f"{key}: {info[key]}")
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
                        app.write_box("\nInvalid input, please try again.")
                        continue 
                    info["first_run"] = "false"    
                    with open("alert_api_preferences.json", "w") as f:
                        json.dump(info, f, indent=4)
                        app.write_box("\nPreferences updated successfully!\nNew Preferences:")
                        for key in keys:
                            app.write_box(f"{key}: {info[key]}")
                        break
            else:
                if info["first_run"] == "false":
                    return True
                else:    
                    return False   
    except FileNotFoundError:
        app.write_box("\nRebuilding alert_api_preferences.json")
        rebuild(program, "alert")
        if program == "main-control":
            return False 
    except json.JSONDecodeError:
        app.write_box("\nInvalid json, rebuilding from scratch")
        os.remove("alert_api_preferences.json")
        rebuild(program, "alert")
        if program == "main-control":
            return False  
def schedule_preferences(app, program):
    keys = {"virus_check", "quarantine"}
    values = {"false", "manual", "true"}
    try:
        with open("schedule_pref.json", "r") as f:
            info = json.load(f)
        check_key = keys.issubset(info.keys())
        check_values = check_key and all(info.get(val) in values for val in keys)
        if not check_values:
            app.write_box("Missing or invalid values, deleting file and rebuilding.")
            os.remove("schedule_pref.json")
            rebuild(program, "schedule")
            if program == "main-control":
                return False 
        else:
                app.write_box("\nPreferences file validated, printing current settings.")
                for key in keys:
                    app.write_box(f"{key}: {info[key]}")
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
                           app.write_box("\nPlease select from the following options:")
                           sel_2 = questionary.select(
                                   "\nPlease select from the following options:",
                                   "\nA.)Auto-Quarantine\nB.)Disable Quarantining\nC.)Manually Decide to Quarantine\nD.)None, Exit\n",
                                   choices=["A", "B", "C", "D"]
                           ).ask()   
                           match sel_2:
                               case "A":
                                   info["quarantine"] = "true"  
                                   app.write_box("\nAuto-Quarantine Enabled")
                                   break  
                               case "B":
                                   info["quarantine"] = "false"
                                   app.write_box("\nAuto-Quarantine Disabled")
                                   break
                               case "C":
                                   info["quarantine"] = "manual"
                                   app.write_box("\nManual Quarantining Enabled")
                                   break
                               case "D":
                                   break
                               case _:
                                   app.write_box("\nInvalid input, please try again")   
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
                                   app.write_box("\nInvalid input, please try again")   
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
                        app.write_box("\nInvalid input, please try again.")
                        continue 
                    with open("schedule_pref.json", "w") as f:
                        json.dump(info, f, indent=4)
                        app.write_box("\nPreferences updated successfully!\nNew Preferences:")
                        for key in keys:
                            app.write_box(f"{key}: {info[key]}")
                        break
    except FileNotFoundError:
        app.write_box("\nRebuilding schedule_pref.json")
        rebuild(program, "schedule")
        if program == "main-control":
            return False 
    except json.JSONDecodeError:
        app.write_box("\nInvalid json, rebuilding from scratch")
        os.remove("schedule_pref.json")
        rebuild(program, "schedule")
        if program == "main-control":
            return False 
def azure_verify(app):
    logging.basicConfig(level=logging.INFO, filename="manifest_cloud.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.transport").setLevel(logging.WARNING)
    azure_connection_string = os.getenv("AZURE_CONNECT_STR")
    azure_container_name = os.getenv("AZURE_CONTAINER")
    azure_container_name_2 = os.getenv("AZURE_CONTAINER_QUARANTINE")
    azure_container_target = os.getenv("AZURE_CONTAINER_TARGET")
    if not azure_connection_string:
       app.write_box("Error: AZURE_CONNECT_STR not found. Please create a .env file based on .env example")
       return
    if not azure_container_name:
       app.write_box("Error: AZURE_CONTAINER not found. Please create a .env file based on .env example")
       return
    if not azure_container_name_2:
       app.write_box("Error: AZURE_CONTAINER_QUARANTINE not found. Please create a .env file based on .env example")
       return
    if not azure_container_target:
        app.write_box("Error: AZURE_CONTAINER_TARGET not found. Please create a .env file based on .env example")
        return
    try:
       blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
       app.write_box("Connection to Azure Blob Storage was successful...")
       container_client = blob_service_client.get_container_client(container=azure_container_name)
       if not container_client.exists():
          app.write_box(f"Connection to source container {azure_container_name} was not successful.")
          return
       else:
          app.write_box(f"Connection to source container {azure_container_name} was successful.")
       container_client_2 = blob_service_client.get_container_client(container=azure_container_name_2)
       if not container_client_2.exists():
          app.write_box(f"Connection to quarantine container {azure_container_name_2} was not successful.")
          return
       else:
         app.write_box(f"Connection to quarantine container {azure_container_name_2} was successful.")
         container_client_target = blob_service_client.get_container_client(container=azure_container_target)
         if not container_client_target.exists():
            app.write_box(f"Connection to target container {azure_container_target} was not successful.")
            return
         else:
            app.write_box(f"Connection to target container {azure_container_target} was successful.")
    except HttpResponseError as e:
        app.write_box(f"Azure Container Error: {e.status_code}: {e.message}")
        logging.error(f"Azure Container Error: {e.status_code}: {e}")
    except Exception as e:
        app.write_box(f"Unexpected Azure Error: {e}")
        logging.error(f"Unexpected Azure Error: {e}")
def local_notification_check(app, program): 
    #This function is now synchronous, WINRT will always complain regardless of what I attempt with async,
    #making the program look like an error has happened when it hasn't. Even suppressing the warning does not work since that
    #is deprecated, as such this has been modified accordingly. It now uses the plyer notifications library, which is
    #also cross-platform.
    if program == "main-control" and not app_state["local_notif"]:
        app.write_box("Desktop notifications are disabled.")  
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
    app.write_box("\nIf a message did not appear on your screen, it is likely notifications are disabled. \nPlease enable them or visit: https://pypi.org/project/plyer/")
    # noinspection inconsistent-returns
    if program == "main-control":
        return True
def webhook_check(app, program):
    if program == "main-control" and not app_state["webhook_notif"]:
        app.write_box("Webhook alerts are disabled.")  
        time.sleep(2)
        return False 
    webhook_id = os.getenv("WEBHOOK")
    if webhook_id is None:
       app.write_box("Error: WEBHOOK not found. Please create a .env file based on .env.example")
       if program == "main-control":
          app.write_box("Webhook alerts are disabled.")  
          time.sleep(2)
          return False
       # noinspection inconsistent-returns
       return
    url = urlparse(webhook_id)
    if not url.scheme or not url.netloc:
       app.write_box("Invalid webhook URL format, please check .env.")
       if program == "main-control":
          app.write_box("Webhook alerts are disabled.")  
          time.sleep(2)
          return False
       # noinspection inconsistent-returns
       return
    try:
        response = requests.get(webhook_id, timeout=5) #Modified because in testing the program
        #I realized it would be annoying to constantly receive message that it is working, instead of critical messages.
        if response and response.status_code in (200, 204):
            app.write_box("Webhook was successful!")
            if program == "main-control":
               return True
            # noinspection inconsistent-returns
            return
        else:
            app.write_box("Invalid webhook or connection error, please check .env.")
            if program == "main-control":
               app.write_box("Webhook alerts are disabled.")  
               time.sleep(2)
               return False
            # noinspection inconsistent-returns
            return
    except Exception:
        app.write_box(f"Invalid webhook or connection error, please check .env and loginfo.log.")
        if program == "main-control":
           app.write_box("Webhook alerts are disabled.")  
           time.sleep(2)
           return False
        # noinspection inconsistent-returns
        return
def vt_check(app, program):
       if program == "main-control" and not app_state["vt_check"]:
           app.write_box("Checking the hash with VirusTotal API is disabled.")  
           time.sleep(2)
           return False 
       app.write_box("Please wait while the program connects to the VirusTotal API.")
       time.sleep(2)
       hash_in = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f" #A SHA-256 hash of a known safe virus.
       base_url = os.getenv("URL")
       api_key = os.getenv("APIKEY")
       # noinspection bad-argument-type
       url = urlparse(base_url)
       if not api_key:
           if program == "notify":
              app.write_box("Error: APIKEY not found. Please create a .env file based on .env.example")
              exit()
           elif program == "main-control":
              app.write_box("Error: APIKEY not found. Please create a .env file based on .env.example")
              app.write_box("The program will run in 2 seconds, but checking the hash with VirusTotal API will be disabled.")  
              time.sleep(2)
              return False
       if not base_url or not url.scheme or not url.netloc:
           if program == "notify":
              app.write_box("Error: URL not found. Please create a .env file based on .env.example")
              exit() 
           elif program == "main-control":
              app.write_box("Error: URL not found. Please create a .env file based on .env.example") 
              app.write_box("The program will run in 2 seconds, but checking the hash with VirusTotal API will be disabled.")  
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
                    app.write_box("Rate limit reached. Please wait a moment.")
                    # noinspection inconsistent-returns
                    return
               elif program == "main-control":
                    app.write_box("Rate limit reached. Please wait a couple of seconds.")
                    time.sleep(5)
                    return True
           elif response.status_code == 401:
               if program == "notify":
                    app.write_box("Authentication Error: Invalid API key.")
                    # noinspection inconsistent-returns
                    return
               elif program == "main-control":
                    app.write_box("Authentication Error: Invalid API key.")
                    app.write_box("The program will run in 2 seconds, but checking the hash with VirusTotal API will be disabled.")  
                    time.sleep(2)
                    return False
           elif response.status_code == 404:
               if program == "notify":
                    app.write_box("Connection to VirusTotal API was not successful.")
                    # noinspection inconsistent-returns
                    return
               elif program == "main-control":
                    app.write_box("Connection to VirusTotal API was not successful.")
                    app.write_box("The program will run in 2 seconds, but checking the hash with VirusTotal API will be disabled.")  
                    time.sleep(2)
                    return False
           if program == "main-control":
              app.write_box("The program successfully connected to the VirusTotal API.")
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
           app.write_box(f"Name: {name}")
           app.write_box(f"Name: {hash_in}")
           app.write_box(f"Is this malicious: {status} by ({malicious_count} detections)")
       except requests.exceptions.RequestException as e:
           app.write_box(f"API Error: {e}")
           if program == "main-control":
              app.write_box("Checking the hash with VirusTotal API is disabled.")  
              time.sleep(2)
              return False 
class notify_window(ctk.CTkToplevel):
      def __init__(self, parent):
            super().__init__(parent)
            self.parent = parent
            self.geometry("900x500")
            self.title("Setup Manager")
            self.resizable(False, False)
            self.protocol("WM_DELETE_WINDOW", self.close_mode_c)
            self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.left_frame.grid(
                row=0,
                column=0,
                columnspan=2,
                rowspan=7,
                sticky="nsew"
            )
            self.title_label = ctk.CTkLabel(
            self.left_frame,
            text="Setup Manager for 3-2-1 Sync-Done!",
            font=("Helvetica", 20, "bold"),
            text_color="#ffffff"
            )
            self.title_label.grid(
                row=0,
                column=0,
                columnspan=2,
                padx=20,
                pady=(20, 20),
                sticky="ew"
            )
            self.menu_text = ctk.CTkTextbox(self.left_frame, width=400, height=250, corner_radius=0, wrap="word")
            self.menu_text.grid(row=1, column=0, columnspan=2, sticky="nsew")
            self.menu_text.insert("0.0", "Welcome to the setup verification menu. \nFrom here, you can check if all services "
             "such as Desktop Notifications, connecting to VirusTotal's API, or Azure Blob Storage Credentials are working the way you intend them to."
            "\n\nPlease select from the following options:"
            "\nA.)Desktop Notifications Check"
            "\nB.)Discord Webhook Integration Check"
            "\nC.)VirusTotal API Check"
            "\nD.)Set Alert Preferences"
            "\nE.)Azure Blob Storage Check"
            "\nF.)Set Auto-Schedule Preferences"
            "\nG.)Set Time and Timezone for Schedule"
            "\nH.)Return to the Main Menu")
            self.menu_text.configure(state="disabled")
            self.message_box = ctk.CTkTextbox(self, width=280,corner_radius=0, wrap="word")
            self.message_box.grid(
                row=0,
                column=2,
                rowspan=7,
                padx=(0, 0),
                pady=0,
                sticky="nsew"
                )
            self.time = ctk.CTkEntry(
                self.left_frame,
                placeholder_text="Exclusive to Option G: Set Time (24 HOURS, FORMAT: HH:MM)"
            )
            self.time.grid(
                row=2,
                column=0,
                columnspan=1,
                padx=(5, 0),
                pady=(5, 0),
                sticky="ew"
            )
            self.time.configure(state="disabled")
            self.time_button = ctk.CTkButton(
            self.left_frame,
            text="Set Time"
            )
            self.time_button.grid(
                row=2,
                column=1,
                padx=(5, 5),
                pady=(5, 0)
            )
            self.time_button.configure(state="disabled")
            self.left_frame.grid_columnconfigure(0, weight=1)
            self.left_frame.grid_columnconfigure(1, weight=0)
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure(2, weight=1)
            self.grid_rowconfigure(1, weight=1)
            msg = "When the program runs, you will see relevant information here. \nTo temporarily check previous events, scroll up. \nTo view and analyze program events across different dates and times, please check the relevant log file."
            self.message_box.insert("end", "\n" + msg)
            self.message_box.configure(state="disabled")
      def close_mode_c(self):
            self.destroy()
            self.parent.deiconify()
#https://pypi.org/project/discord-webhook/
#https://pypi.org/project/plyer/
#https://pypi.org/project/chime/