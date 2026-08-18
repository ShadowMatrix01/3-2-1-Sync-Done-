# 3-2-1-Sync-Done!
## Project Overview
3-2-1, Sync Done! Demonstrates core data protection strategies in a practical way. It is a companion to the industry standard 3-2-1 data backup policy and focuses on data integrity. The project uses scripts, cloud and local storage, health checks, and storage alerts to support these principles and help prevent hardware failure, bit rot, ransomware, file tampering, synchronization failures, software bugs, and human error. 

-----------------------------------------------------------------------------------------------
## DISCLAIMER, AND SETUP INSTRUCTIONS
**TLDR**: Use the following format in your .env file.

URL=https://www.virustotal.com/api/v3/files/

APIKEY=YOUR_APIKEY

WEBHOOK=YOUR_WEBHOOK

AZURE_CONNECT_STR=YOUR_AZURE_CONNECTION_STRING

AZURE_CONTAINER=YOUR_AZURE_CONTAINER_NAME

AZURE_CONTAINER_QUARANTINE=YOUR_AZURE_QUARANTINE_CONTAINER_NAME

**VirusTotal API DISCLAIMER:** This project includes optional integration with the VirusTotal API. This tool is a file integrity auditor. It is **not** an antivirus. It does not actively monitor your computer for viruses, and is only allowed to move files to a "quarantine" folder. This is due to VirusTotal's Terms of Service, as such, please keep this in mind. Usage of this feature is entirely at the user's discretion and is subject to VirusTotal's Terms of Service. The developer of this tool assumes no liability for the user's compliance with these terms or for the API's rate-limiting policies.
**You must supply your own VirusTotal key in your own .env file.**
Ensure the VirusTotal API is working by running Mode C, and select option C from the menu. 
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
8. Ensure the webhook is working by running Mode C, and select option B from the menu.
9. After verification is successful, you are done!

**Azure Storage Blobs Setup**


------------------------------------------------------------------------------------------------
### Language 
This project is being made with **Python 3.12.1**, and as such uses tools and frameworks connected to Python. 
### Tools
Common tools in use include JavaScript Object Notation (**JSON**) for the manifest, the hashlib library for hashing files in the **SHA-256 (Secure Hash Algorithm 256-bit)** format, and the built-in logging module which directly outputs detailed information to loginfo.log.  It is quite likely that more tools will be used as the project expands in scope, especially when seamless online and local integration is added. 
### Frameworks/API/SDK/Other
Plyer 2.1.0 and discord-webhook 1.4.1 are libraries that have been added to handle corrupted, tampered, and potentially malicious files by ensuring the user is not only immediately notified of an issue in the program itself, but also through the operating system's notification system and across multiple devices simultaneously through the use of Discord webhooks. This ensures that the user has a detailed log that they can reference later, should new or unusual behaviors be detected from a file or a blob, as well as ensuring the user's attention is immediately grabbed when a file is under review by the program. Plyer 2.1.0 is cross-platform, meaning that notifications will work between Windows, MacOS, and Linux. 

Please note, Discord webhooks require a free Discord account. For more information, please click here: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

Chime 0.8.0 is a a simple auditory cue system that is cross compatible across different operating systems. This was added because sounds are not included with plyer, and I felt that auditory cues are needed.

This project uses the Microsoft Azure Blob Storage SDK (azure-core 1.41.0 and azure-storage-blob 12.30.0) for the application's cloud features.  Azure Blob Storage uses data lakes, machine learning, and scalable technologies to ensure optimal performance with stored blobs. My application allows blobs (unstructured cloud files) to be hashed directly within the application. In addition to this, the 3-2-1-Sync-Done! application allows the same functionality present in the local version (hashing, scanning, moving, quarantining, logging, etc.) to be used with the cloud version. To utilize this, you **must** ensure that you have both a free Azure account and an Azure Blob Storage Account. In this account, you must have at least two containers; one of these is a normal container where blobs (files) will be stored. The other is the quarantine container, which is where potentially dangerous blobs will be moved to with a corresponding log. You **must** ensure that these are put in the corresponding fields in the .env file, as mixing them up will result in normal blobs and potentially dangerous blobs being put in the wrong place.

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

### Check if Local Notifications, Discord Webhook, and VirusTotal API are working as intended, MODE C.

Mode C allows you to check before running the program if everything is setup correctly. Mode C only requires two arguments, which are --source and --mode "C". However, unlike the other modes, source should be an empty string with a space " " since the program does not require a path to verify program functionality. To run this mode, simply enter the following into your terminal:

#### Windows
Run this command: **python main-control.py --source " " --mode "C"**
#### macOS / Linux
Run this command: **python3 main-control.py --source " " --mode "C"**

From here, you will be prompted to select an option from a menu, please type the corresponding character.

**A. Desktop Notifications Check**

**B. Discord Webhook Integration Check**

**C. VirusTotal API Check**

**D. Set Alert Preferences**

**E. Exit the Menu**
### Hashing Files On The Cloud and Checking Intregrity Of Files On The Cloud, MODE D.
Ensure that your .env file is setup correctly before running the program. While the program can detect if improperly formatted fields and invalid credentials are supplied, it **CANNOT** detect if containers you supplied are flipped or the incorrect containers. Please verify this, as it may be quite tedious to manually move and delete blobs back to their intended location after the fact.

Mode D allows you to hash, verify, move, delete, and quarantine blobs from the cloud. Mode D only requires two arguments, which are --source and --mode "D". Just like mode C, source should be an empty string with a space " " since the program does not require a path to verify program functionality. To run this mode, simply enter the following into your terminal:

#### Windows
Run this command: **python main-control.py --source " " --mode "D"**
#### macOS / Linux
Run this command: **python3 main-control.py --source " " --mode "D"**

Please follow any input prompts the program may give you. If notifications and webhooks are setup, you will recieve notifications and webhooks when your input is needed.

-----------------------------------------------------------------------------------------------
## Miscellaneous
At this stage of the project, I cannot make any promises that all features I intend to add will be able to be done. If this is the case, this ReadMe.md will be updated accordingly. This tool is for diagnostic purposes only and does not provide data recovery services. If data loss or corruption is detected, users should rely on their established backup restoration procedures or professional data recovery services. Thank you! 
### **LAST UPDATED: August 18th, 2026.**
