
import os
from dotenv import load_dotenv
import requests
import asyncio
import time
from desktop_notifier import DesktopNotifier, Urgency, Button, DEFAULT_SOUND
from discord_webhook import DiscordWebhook,  DiscordEmbed
from urllib.parse import urlparse 
load_dotenv()
def main_menu():
    while True:
        print("\nWelcome to the setup verification menu. \nFrom here, you can check if all three external services" 
        " like Desktop Notifications, Discord Webhook Integration, and VirusTotal API are working.")
        sel = input("\nPlease select from the following options by typing the corresponding letter:\nA.Desktop Notifications Check\nB.Discord Webhook Integration\nC.VirusTotal API\n")
        if sel.strip().upper() == "A":
           local_notification_check()
           break
        elif sel.strip().upper()  == "B":
           webhook_check()
           break
        elif sel.strip().upper()  == "C":
           VT_check()
           break
        else:
           print("Invalid input. Please try again.")
           continue
def local_notification_check():
    async def main() -> None:
       notifier = DesktopNotifier(app_name="3-2-1-Sync-Done!")
       await notifier.send(title="3-2-1-Sync-Done!", 
                           message="A Data Integrity Solution.",
                           urgency=Urgency.Normal,
                           buttons=[
                              Button(
                                 title="Okay",
                                 on_pressed=lambda: print("Notifications are working!")
                                 )
                           ],
                           sound=DEFAULT_SOUND)
    asyncio.run(main())
    print("\nIf a message did not appear on your screen, it is likely notifications are disabled. \nPlease enable them or visit: https://pypi.org/project/desktop-notifier/ ")
def webhook_check():
    webhook_id = os.getenv("WEBHOOK")
    if webhook_id is None:
       print("Error: WEBHOOK not found. Please create a .env file based on .env.example")
       return
    url = urlparse(webhook_id)
    if not url.scheme or not url.netloc:
       print("Invalid webhook URL format, please check .env.")
       return
    try:
        webhook = DiscordWebhook(url=webhook_id, rate_limit_retry=True)
        msg = DiscordEmbed(title="3-2-1-Sync-Done!", description="Webhook is functional! \nIn normal use, this would be red and have more information.", color="00FF00")
        webhook.add_embed(msg)
        response = webhook.execute()
        if response and response.status_code in (200, 204):
            print("Webhook was successful! Please check your Discord server.")
            return
        else:
            print("Invalid webhook or connection error, please check .env.")
            return
    except Exception:
        print(f"Invalid webhook or connection error, please check .env and loginfo.log.")
        return
def VT_check():
       print("Please wait while the program connects to the VirusTotal API.")
       time.sleep(5)
       hash = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f" #A SHA-256 hash of a known safe virus.
       base_url = os.getenv("URL")
       api_key = os.getenv("APIKEY")
       if not api_key:
           print("Error: APIKEY not found. Please create a .env file based on .env.example")
           exit(1)
       if not base_url:
           print("Error: URL not found. Please create a .env file based on .env.example")
           exit(1) 
       full_url = f"{base_url}{hash}"
       headers = {"accept": "application/json", 
                   "x-apikey": api_key}
       try:
           response = requests.get(full_url, headers=headers)
           if response.status_code == 429:
               print("Rate limit reached. Please wait a moment.")
               return
           elif response.status_code == 401:
               print("Authentication Error: Invalid API key.")
               return
           elif response.status_code == 404:
               print("Connection to VirusTotal API was not successful.")
               return
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
#https://pypi.org/project/discord-webhook/
#https://pypi.org/project/desktop-notifier/