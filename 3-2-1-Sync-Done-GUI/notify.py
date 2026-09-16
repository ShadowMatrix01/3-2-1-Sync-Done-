import os
from dotenv import load_dotenv
import requests
import time
import json
import chime
import logging
import re
import customtkinter as ctk
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
from plyer import notification #now synchronous with plyer.
from urllib.parse import urlparse 
from pathlib import Path
from dotenv import set_key
from timezones import timezones_from_file
from discord_webhook import DiscordWebhook,  DiscordEmbed
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
    env_file = Path(".env")
    load_dotenv(env_file, override=True)
    local_time = app.local_time.get()
    cloud_time = app.cloud_time.get()
    timezone = app.timezone_dropdown.get()
    if timezone == "Please select a timezone:":
       app.write_box("Error! You must select a valid timezone.")
       return
    if not fmt(local_time):
        app.write_box("Error! Invalid local time. Use HH:MM, 24 HOUR FORMAT.")
        return
    if not fmt(cloud_time):
        app.write_box("Error! Invalid cloud time. Use HH:MM, 24 HOUR FORMAT.")
        return
    set_key(
        dotenv_path=env_file,
        key_to_set="TIME_IN_24_HOURS_LOCAL",
        value_to_set=local_time
    )
    set_key(
        dotenv_path=env_file,
        key_to_set="TIME_IN_24_HOURS_CLOUD",
        value_to_set=cloud_time
    )
    set_key(
        dotenv_path=env_file,
        key_to_set="TIMEZONE_DST_AWARE",
        value_to_set=timezone
    )
    app.write_box(
        f"Local Time: {local_time}\n"
        f"Cloud Time: {cloud_time}\n"
        f"Timezone: {timezone}\n"
        "Schedule settings updated successfully."
    )
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
               return
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
def save_alert_preferences(app):
    global app_state
    try:
        with open("alert_api_preferences.json", "r") as f:
            info = json.load(f)
        info["webhook_alerts"] = app.webhook_dropdown.get()
        info["local_alerts"] = app.local_dropdown.get()
        info["virus_total_check"] = app.vt_dropdown.get()
        info["first_run"] = "false"
        with open("alert_api_preferences.json", "w") as f:
            json.dump(info, f, indent=4)
        app_state["local_notif"] = (
            info["local_alerts"] == "true"
        )
        app_state["webhook_notif"] = (
            info["webhook_alerts"] == "true"
        )
        app_state["vt_check"] = (
            info["virus_total_check"] == "true"
        )
        app.write_box("\nPreferences updated successfully!")
        app.write_box("New Preferences:")
        for key in info:
            app.write_box(f"{key}: {info[key]}")
    except FileNotFoundError:
        app.write_box("Error! alert_api_preferences.json was not found.")
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
                app.write_box("\nSchedule preferences loaded into the GUI.")
                return
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
def save_schedule_preferences(app):
    try:
        with open("schedule_pref.json", "r") as f:
            info = json.load(f)
        info["quarantine"] = app.quarantine_dropdown.get()
        info["virus_check"] = app.virus_check_dropdown.get()
        with open("schedule_pref.json", "w") as f:
            json.dump(info, f, indent=4)
        app.write_box("\nPreferences updated successfully!")
        app.write_box("New Preferences:")
        for key in info:
            app.write_box(f"{key}: {info[key]}")
    except FileNotFoundError:
        app.write_box("Error! schedule_pref.json was not found.")
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
       app.write_box("\nConnection to Azure Blob Storage was successful.")
       container_client = blob_service_client.get_container_client(container=azure_container_name)
       if not container_client.exists():
          app.write_box(f"\nConnection to source container {azure_container_name} was not successful.")
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
        if program == "main-control":
            response = requests.get(webhook_id, timeout=5) #Modified because in testing the program
            #I realized it would be annoying to constantly receive message that it is working, instead of critical messages.
        else:
            webhook = DiscordWebhook(url=webhook_id, rate_limit_retry=True)
            msg = DiscordEmbed(title="3-2-1-Sync-Done!", description=f"A Data Integrity Solution:\nHash and Verify Files\nSecurely Move Important Files\nCloud Integration and More!", color="FFD700")
            webhook.add_embed(msg)
            response = webhook.execute()
        if response and response.status_code in (200, 204):
            app.write_box("\nWebhook was successful! Please check your discord server. \nIf nothing showed up in your server, please visit:\nhttps://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks ")
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
       app.write_box("\nPlease wait while the program connects to the VirusTotal API.")
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
                    app.write_box("\nConnection to VirusTotal API was not successful.")
                    # noinspection inconsistent-returns
                    return
               elif program == "main-control":
                    app.write_box("\nConnection to VirusTotal API was not successful.")
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
            self.withdraw()
            #Workaround I had to do since the GUi would look off while the timezone file
            #was being loaded, allows the window to be drawn before being shown.
            global sel
            sel = "A"
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
            self.local_time = ctk.CTkEntry(
            self.left_frame,
            placeholder_text="MODE G: Local Time, 24 HOUR FORMAT (HH:MM)"
            )
            self.local_time.grid(
                row=2,
                column=0,
                columnspan=2,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            self.cloud_time = ctk.CTkEntry(
                self.left_frame,
                placeholder_text="MODE G: Cloud Time, 24 HOUR FORMAT (HH:MM)"
            )
            self.cloud_time.grid(
                row=3,
                column=0,
                columnspan=2,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            self.local_time.configure(state="disabled")
            self.cloud_time.configure(state="disabled")
            self.timezone_dropdown = ctk.CTkOptionMenu(
                self.left_frame,
                values=timezones_from_file()
            )
            self.timezone_dropdown.grid(
                row=4,
                column=0,
                padx=(5, 5),
                pady=(5, 5),
                sticky="ew"
            )
            self.timezone_dropdown.set(
                "Please select a timezone:"
            )
            self.dropdown = ctk.CTkOptionMenu(
                master=self.left_frame,
                values=["A.)Desktop Notifications Check",
                        "B.)Discord Webhook Integration Check",
                        "C.)VirusTotal API Check",
                        "D.)Set Alert Preferences",
                        "E.)Azure Blob Storage Check",
                        "F.)Set Auto-Schedule Preferences",
                        "G.)Set Time and Timezone for Schedule",
                        "H.)Return to the Main Menu"],
                command=self.mode_return
            )
            self.dropdown.grid(row=5, column=0, padx=(5,5), pady=(5,5), sticky="w")
            self.dropdown.set("A.)Desktop Notifications Check") #Added to prevent edge case that was crashing the program.
            self.button = ctk.CTkButton(self.left_frame, text="Verify/Modify/Exit", command=self.submit)
            self.button.grid(row=5,column=1, padx=0, pady=20, sticky="e")
            self.time_button = ctk.CTkButton(self.left_frame, text="Set Time")
            self.time_button.grid(
                row=4,
                column=1,
                padx=0,
                pady=(0, 0)
            )
            self.time_button.configure(state="disabled")
            self.webhook_dropdown = ctk.CTkOptionMenu(
            self.left_frame,
            values=["Enable Webhook Notifications?", "true", "false"]
            )
            self.local_dropdown = ctk.CTkOptionMenu(
                self.left_frame,
                values=["Enable Desktop Notifications?", "true", "false"]
            )
            self.vt_dropdown = ctk.CTkOptionMenu(
                self.left_frame,
                values=["Enable VirusTotal Checks?", "true", "false"]
            )
            self.quarantine_dropdown = ctk.CTkOptionMenu(
                self.left_frame,
                values=["Auto-Quarantine Files/Blobs?", "true", "false", "manual"]
            )
            self.virus_check_dropdown = ctk.CTkOptionMenu(
                self.left_frame,
                values=["Auto-Check Files/Blobs with VirusTotal?", "true", "false", "manual"]
            )
            self.webhook_dropdown.grid_remove()
            self.local_dropdown.grid_remove()
            self.vt_dropdown.grid_remove()
            self.quarantine_dropdown.grid_remove()
            self.virus_check_dropdown.grid_remove()
            self.left_frame.grid_columnconfigure(0, weight=1)
            self.left_frame.grid_columnconfigure(1, weight=0)
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure(2, weight=1)
            self.grid_rowconfigure(1, weight=1)
            msg = "When the program runs, you will see relevant information here. \nTo temporarily check previous events, scroll up. \nTo view and analyze program events across different dates and times, please check the relevant log file."
            self.message_box.insert("end", "\n" + msg)
            self.message_box.configure(state="disabled")
            self.deiconify()
      def mode_return(self, value):
         global sel
         self.local_time.grid_remove()
         self.cloud_time.grid_remove()
         self.timezone_dropdown.grid_remove()
         self.time_button.grid_remove()
         self.webhook_dropdown.grid_remove()
         self.local_dropdown.grid_remove()
         self.vt_dropdown.grid_remove()
         self.quarantine_dropdown.grid_remove()
         self.virus_check_dropdown.grid_remove()
         self.local_time.configure(state="disabled")
         self.cloud_time.configure(state="disabled")
         if value == "A.)Desktop Notifications Check":
            sel = "A"
         elif value == "B.)Discord Webhook Integration Check":
            sel = "B"
         elif value == "C.)VirusTotal API Check":
            sel = "C"
         elif value == "D.)Set Alert Preferences":
            sel = "D"
            self.webhook_dropdown.grid(
                row=2,
                column=0,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            self.local_dropdown.grid(
                row=3,
                column=0,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            self.vt_dropdown.grid(
                row=4,
                column=0,
                padx=(5, 5),
                pady=(5, 5),
                sticky="ew"
            )
            alert_preferences(self, "notify")
         elif value == "E.)Azure Blob Storage Check":
            sel = "E"
         elif value == "F.)Set Auto-Schedule Preferences":
            sel = "F"
            self.quarantine_dropdown.grid(
                row=2,
                column=0,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            self.virus_check_dropdown.grid(
                row=3,
                column=0,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            schedule_preferences(self, "notify")
         elif value == "G.)Set Time and Timezone for Schedule":
            sel = "G"
            self.local_time.grid(
                row=2,
                column=0,
                columnspan=2,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            self.cloud_time.grid(
                row=3,
                column=0,
                columnspan=2,
                padx=(5, 5),
                pady=(5, 0),
                sticky="ew"
            )
            self.timezone_dropdown.grid(
                row=4,
                column=0,
                padx=(5, 5),
                pady=(5, 5),
                sticky="ew"
            )
            self.time_button.grid(
                row=4,
                column=1,
                padx=0,
                pady=0
            )
            self.local_time.configure(state="normal")
            self.cloud_time.configure(state="normal")
         elif value == "H.)Return to the Main Menu":
            sel = "H"
      def write_box(self, message):
        self.after(
                0,
                lambda: (
                self.message_box.configure(state="normal"),
                self.message_box.insert("end", "\n" + message),
                self.message_box.see("end"),
                self.message_box.configure(state="disabled")
                )
        )
      def submit(self):
        global program
        program = "notify"
        self.button.configure(state="disabled")
        if sel == "A":
           local_notification_check(self, program)
        elif sel  == "B":
           webhook_check(self, program)
        elif sel  == "C":
           vt_check(self, program)
        elif sel == "D":
           save_alert_preferences(self)
        elif sel == "E":
           azure_verify(self)
        elif sel == "F":
           save_schedule_preferences(self)
        elif sel == "G":
           schedule_time(self)
        elif sel == "H":
            self.destroy()
            self.parent.deiconify()
        else:
           self.write_box("Invalid input. Please try again.")
        self.button.configure(state="normal")
      def close_mode_c(self):
          self.destroy()
          self.parent.deiconify()
#https://pypi.org/project/discord-webhook/
#https://pypi.org/project/plyer/
#https://pypi.org/project/chime/