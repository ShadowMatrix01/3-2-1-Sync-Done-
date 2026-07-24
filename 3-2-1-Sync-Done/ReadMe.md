# 3-2-1-Sync-Done!
## Project Overview
3-2-1, Sync Done! Demonstrates core data protection strategies in a practical way. It is a companion to the industry standard 3-2-1 data backup policy and focuses on data integrity. The project uses scripts, cloud and local storage, health checks, and storage alerts to support these principles and help prevent hardware failure, bit rot, ransomware, file tampering, synchronization failures, software bugs, and human error. 

-----------------------------------------------------------------------------------------------
## DISCLAIMER, AND SETUP INSTRUCTIONS
**VirusTotal API DISCLAIMER:** This project includes optional integration with the VirusTotal API. This tool is a file integrity auditor. It is **not** an antivirus. It does not actively monitor your computer for viruses, and is only allowed to move files to a "quarantine" folder. This is due to VirusTotal's Terms of Service, as such, please keep this in mind. Usage of this feature is entirely at the user's discretion and is subject to VirusTotal's Terms of Service. The developer of this tool assumes no liability for the user's compliance with these terms or for the API's rate-limiting policies.
**You must supply your own VirusTotal key in your own .env file. Through the terminal, head to where the program is located. Then use the command touch .env to create the .env file. In this .env file, use the following format:**
1. URL=https://www.virustotal.com/api/v3/files/
2. APIKEY=YOURAPIKEY

**Do NOT include the numbers 1 or 2. Put each field on its own line, and ensure no spaces between the equal sign, before the key, and after the value.**

Ensure the VirusTotal API is working by running Mode 3B, and select option 2 from the menu. 
For more information, please visit: https://docs.virustotal.com/docs/api-overview. 

**Discord Webhook Setup:** 
To receive notifications from the app in Discord, please follow these steps:
1. Open your Discord server.
2. Go to Server Settings → Integrations → Webhooks.
3. Click Create Webhook.
4. Give the webhook a name.
5. Select the channel where you want notifications to appear.
6. Click Copy Webhook URL.
7. In the **.env** file, add this: WEBHOOK=yourdiscordwebhook and save.
8. Ensure the webhook is working by running Mode 3B, and select option 3 from the menu.
9. After verification is successful, you are done!
------------------------------------------------------------------------------------------------
### Language 
This project is being made with **Python 3.12.1**, and as such uses tools and frameworks connected to Python. 
### Tools
Common tools in use include JavaScript Object Notation (**JSON**) for the manifest, the hashlib library for hashing files in the **SHA-256 (Secure Hash Algorithm 256-bit)** format, and the built-in logging module which directly outputs detailed information to loginfo.log.  It is quite likely that more tools will be used as the project expands in scope, especially when seamless online and local integration is added. 
### Frameworks/API/Other
Desktop-notifier 6.2.0 and discord-webhook 1.4.1 are libraries that have been added to handle corrupted, tampered, and potentially malicious files by ensuring the user is not only immediately notified of an issue in the program itself, but also through the operating system's notification system and across multiple devices simultaneously through the use of Discord webhooks. This ensures that the user has a detailed log that they can reference later, should new or unusual behaviors be detected from an application, as well as ensuring the user's attention is immediately grabbed when a file is under review by the program. Desktop-notifier 6.2.0 is cross-platform, meaning that notifications will work between Windows, MacOS, and Linux. 

Please note, Discord webhooks require a free Discord account. For more information, please click here: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

To ensure connectivity with a cloud data storage provider, the user will have to verify their credentials through a secure connection, and will be done through some SDK or API. This will be made clear as soon as more information is available.

-----------------------------------------------------------------------------------------------
## How To Run

### Hashing Files and Checking Intregrity of Files, MODE A.

#### Windows

To run the 3-2-1 Sync Done! application for hashing files, type the following command into the terminal: **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --mode "A".** If you want to use the program only on files with a specific extension, use: **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".** You **must** provide a directory path, not a specific file path. If this does not work, it is likely because Windows cannot find where Python is installed on your machine. If Python is installed correctly, use this instead: **/c/Users/YOURUSERNAME/AppData/Local/Programs/Python/Python312/python.exe main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".** Please note that --source2 and --ext are optional, while --source and --mode are **required**. You may also be able to run it through cmd as **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".**

#### macOS / Linux

To run the 3-2-1 Sync Done! application for hashing files on macOS or Linux, type the following command into the terminal: **python3 main-control.py --source "/path/to/data" --source2 "/path/to/data" --mode "A".** If you want to use the program only on files with a specific extension, use: **python3 main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".** You **must** provide a directory path, not a specific file path. On most macOS and Linux systems, python3 is the correct command. If python3 does not work, try replacing it with python. Please note that --source2 and --ext are optional, while --source and --mode are **required**.

### Checking the integrity of a specific file in a specific manifest, MODES: 1B and 2B.

To run the 3-2-1 Sync Done! application to verify the integrity of a specific file, you must note the following.

1. First, you must get the specific path to the **FILE** you want to verify. If you supply a directory, such as C:\Users\YOURUSERNAME, it will always fail. The correct usage would be C:\Users\YOURUSERNAME\file.txt on Windows or /home/YOURUSERNAME/file.txt (Linux) or /Users/YOURUSERNAME/file.txt (macOS). This is intentional. Mode A should be used for a complete hashing and verification of a directory, whereas modes 1B and 2B should be used for quickly checking the integrity of a specific file.

2. **Do NOT include --source2 or --ext.** If you do, the program will not work. Instead follow step 3.

3. To check for the file in manifest.json, please use --mode "1B". Otherwise, to check for the file in manifest2.json, please use --mode "2B". 

4. If you see something odd or suspicious, **do NOT overwrite your manifests or delete them**. Instead, manually check the file in question.

5. Improperly formatted JSON will result in the program throwing errors. It is wise to not manually modify the manifest files, and instead copy them and place them somewhere secure, before creating new manifests.

### Check if local notifications, Discord Webhook, and VirusTotal API are working as intended, MODE C.

Mode C allows you to check before running the program if everything is setup correctly. Mode C only requires two arguments, which are --source and --mode "3B". However, unlike the other modes, source should be an empty string "" since the program does not require a path to verify program functionality. To run this mode, simply enter the following into your terminal:

#### Windows
Run this command: **python main-control.py --source "" --mode "C"**
#### macOS / Linux
Run this command: **python3 main-control.py --source "" --mode "C"**

From here, you will be prompted to select an option from a menu, please type the corresponding character.

**A.Desktop Notifications Check**

**B.Discord Webhook Integration**

**C.VirusTotal API**

-----------------------------------------------------------------------------------------------
## Miscellaneous
At this stage of the project, I cannot make any promises that all features I intend to add will be able to be done. If this is the case, this ReadMe.md will be updated accordingly. This tool is for diagnostic purposes only and does not provide data recovery services. If data loss or corruption is detected, users should rely on their established backup restoration procedures or professional data recovery services. Thank you! 
### **LAST UPDATED: July 24th, 2026.**