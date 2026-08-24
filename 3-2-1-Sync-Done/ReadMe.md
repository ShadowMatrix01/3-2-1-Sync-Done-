# 3-2-1-Sync-Done!
## Project Overview
3-2-1, Sync Done! Practically demonstrates core data protection strategies. It complements the industry-standard 3-2-1 data backup policy and focuses on data integrity. The project uses scripts, cloud and local storage, health checks, and storage alerts to support these principles and help prevent hardware failure, data degradation, ransomware, file tampering, synchronization failures, software bugs, and human error. 

-----------------------------------------------------------------------------------------------
## DISCLAIMER AND SETUP INSTRUCTIONS
**TLDR**: Use the following format in your .env file.

URL=https://www.virustotal.com/api/v3/files/

APIKEY=YOUR_APIKEY

WEBHOOK=YOUR_WEBHOOK

AZURE_CONNECT_STR=YOUR_AZURE_CONNECTION_STRING

AZURE_CONTAINER=YOUR_AZURE_CONTAINER_NAME

AZURE_CONTAINER_QUARANTINE=YOUR_AZURE_QUARANTINE_CONTAINER_NAME

TIME_IN_24_HOURS=HH:MM

TIMEZONE_DST_AWARE=YOUR_TIMEZONE

**VirusTotal API DISCLAIMER:** This project includes optional integration with the VirusTotal API. This tool is a file integrity auditor. It is **not** an antivirus. It does not actively monitor your computer for viruses, and is only allowed to move files to a "quarantine" folder. This is due to VirusTotal's Terms of Service; as such, please keep this in mind. Usage of this feature is entirely at the user's discretion and is subject to VirusTotal's Terms of Service. The developer of this tool assumes no liability for the user's compliance with these terms or for the API's rate-limiting policies.
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
After creating your Azure account and your Azure Blob Storage Account, please follow these steps:
1. Log in to the Azure portal and navigate to your storage account.
2. On the left-hand menu, click Access Keys (under Security + networking).
3. Copy the connection string under key1.
4. Put this connection string in the .env file as AZURE_CONNECT_STR=YOUR_AZURE_CONNECTION_STRING
5. Go to containers under data storage in your storage account and create two private containers.
6. Once you have these two containers, put the source container with the blobs in the .env file as AZURE_CONTAINER=YOUR_AZURE_CONTAINER_NAME, and the container for quarantining and logging as AZURE_CONTAINER_QUARANTINE=YOUR_AZURE_QUARANTINE_CONTAINER_NAME


------------------------------------------------------------------------------------------------
### Language 
This project is being made with **Python 3.12.1**, and as such uses tools and frameworks connected to Python. 
### Tools
Common tools in use include JavaScript Object Notation (**JSON**) for the manifest, the hashlib library for hashing files in the **SHA-256 (Secure Hash Algorithm 256-bit)** format, shutil for moving files to quarantine, stat for getting a files metdatata, and the built-in logging module which directly outputs detailed information to loginfo.log. 
### Frameworks/API/SDK/Other
Plyer 2.1.0 and discord-webhook 1.4.1 are libraries added to handle corrupted, tampered, and potentially malicious files. This ensures the user is not only immediately notified of an issue in the program itself, but also through desktop notifications and multiple devices simultaneously via Discord webhooks. This ensures that the user has a detailed log that they can reference later, should new or unusual behaviors be detected from a file or a blob, as well as ensuring the user's attention is immediately grabbed when a file is under review by the program. Plyer 2.1.0 is cross-platform, meaning that notifications will work between Windows, macOS, and Linux. 

Please note, Discord webhooks require a free Discord account. For more information, please click here: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

Chime 0.8.0 is a simple auditory cue system that is cross-compatible across different operating systems. This was added because sounds are not included with plyer, and I felt that auditory cues are needed. For more information, please visit: https://pypi.org/project/chime/

Questionary 2.1.1 is a Python library to build pretty command-line user prompts. For more information please visit: https://pypi.org/project/questionary/

Schedule 1.2.2 runs Python functions (or any other callable) periodically using a friendly syntax. It utilizes a simple-to-use API for scheduling jobs, has an in-process scheduler for periodic jobs, and is lightweight with no external dependencies. It is tested to run on Python 3.7, 3.8, 3.9, 3.10, 3.11, and 3.12. Schedule 1.2.2 uses the 24-hour clock, with the format HH:MM. For more information, please visit: https://pypi.org/project/schedule/

Pytz-2026.3.post1 brings the Olson tz database into Python. This library enables accurate, cross-platform timezone calculations in Python 2.4 or higher. Almost all the Olson time zones are supported. It also solves the issue of ambiguous times at the end of daylight saving time. In this application, I am using it in conjunction with schedule 1.2.2 to ensure that the program can run by itself on a daily basis. My program supports 594 pytz time zones, which can be found in the pytz_timezones.txt file. For more information, please visit: https://pypi.org/project/pytz/

Microsoft Azure Blob Storage SDK (azure-core 1.41.0 and azure-storage-blob 12.30.0) is used for the application's cloud features.  Azure Blob Storage uses data lakes, machine learning, and scalable technologies to ensure optimal performance with stored blobs. My application allows blobs (unstructured cloud files) to be hashed directly within the application. In addition to this, the 3-2-1-Sync-Done! application allows the same functionality present in the local version (hashing, scanning, moving, quarantining, logging, etc.) to be used with the cloud version. To utilize this, you **must** ensure that you have both a free Azure account and an Azure Blob Storage Account. In this account, you must have at least two containers; one of these is a normal container where blobs (files) will be stored. The other is the quarantine container, which is where potentially malicious blobs will be moved to with a corresponding log. You **must** ensure that these are put in the corresponding fields in the .env file, as mixing them up will result in normal blobs and potentially malicious blobs being put in the wrong place.

-----------------------------------------------------------------------------------------------
## How To Run

### Hashing Files and Checking Integrity of Files, MODES A1 and A2.

#### Windows

To run the 3-2-1 Sync Done! application for hashing files, type the following command into the terminal: **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --mode "A1".** If you want to use the program only on files with a specific extension, use: **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A1".** You **must** provide a directory path, not a specific file path. If this does not work, it is likely because Windows cannot find where Python is installed on your machine. If Python is installed correctly, use this instead: **/c/Users/YOURUSERNAME/AppData/Local/Programs/Python/Python312/python.exe main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A1".** Please note that --source2 and --ext are optional, while --source and --mode are **required**. You may also be able to run it through cmd as **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A1".**

#### macOS / Linux

To run the 3-2-1 Sync Done! application for hashing files on macOS or Linux, type the following command into the terminal: **python3 main-control.py --source "/path/to/data" --source2 "/path/to/data" --mode "A1".** If you want to use the program only on files with a specific extension, use: **python3 main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A1".** You **must** provide a directory path, not a specific file path. On most macOS and Linux systems, python3 is the correct command. If python3 does not work, try replacing it with python. Please note that --source2 and --ext are optional, while --source and --mode are **required**.

#### MODE A2

**You may also schedule this to occur every day at a specific time, to do this simply swap --mode "A1" for --mode "A2".**

### Checking the integrity of a specific file in a specific manifest, MODES: 1B and 2B.

To run the 3-2-1 Sync Done! application to verify the integrity of a specific file, you must note the following.

1. First, you must get the specific path to the **FILE** you want to verify. If you supply a directory, such as C:\Users\YOURUSERNAME, it will always fail. The correct usage would be C:\Users\YOURUSERNAME\file.txt on Windows or /home/YOURUSERNAME/file.txt (Linux) or /Users/YOURUSERNAME/file.txt (macOS). This is intentional. Modes A1 and A2 should be used for a complete hashing and verification of a directory, whereas modes 1B and 2B should be used for quickly checking the integrity of a specific file.

2. **Do NOT include --source2 or --ext.** If you do, the program will not work. Instead, follow step 3.

3. To check for the file in manifest.json, please use --mode "1B". Otherwise, to check for the file in manifest2.json, please use --mode "2B". 

4. If you see something odd or suspicious, **do NOT overwrite your manifests or delete them**. Instead, manually check the file in question.

5. Improperly formatted JSON will result in the program throwing errors. It is wise not to manually modify the manifest files, and instead copy them and place them somewhere secure, before creating new manifests.

### Check if Local Notifications, Discord Webhook, Azure Storage Blobs, VirusTotal API are working as intended, Set Alert and Schedule Preferences, and Set Time and Timezone for Schedule, MODE C.
Mode C allows you to check before running the program if everything is set up correctly. Mode C only requires two arguments, which are --source and --mode "C". However, unlike the other modes, source should be an empty string with a space " " since the program does not require a path to verify program functionality. To run this mode, simply enter the following into your terminal:

#### Windows
Run this command: **python main-control.py --source " " --mode "C"**
#### macOS / Linux
Run this command: **python3 main-control.py --source " " --mode "C"**

From here, you will be prompted to select an option from a menu; please use the arrow keys to navigate and press Enter to confirm.

**A. Desktop Notifications Check**

**B. Discord Webhook Integration Check**

**C. VirusTotal API Check**

**D. Set Alert Preferences**

**E. Azure Blob Storage Check**

**F. Set Auto-Schedule Preferences**

**G. Set Time and Timezone for Schedule**

**H. Exit**
### Hashing Files On The Cloud and Checking Integrity Of Files On The Cloud, MODES D1 AND D2.
Ensure that your .env file is set up correctly before running the program. While the program can detect if improperly formatted fields and invalid credentials are supplied, it **CANNOT** detect if containers you supplied are flipped or the incorrect containers. Please verify this, as it may be quite tedious to manually move and delete blobs back to their intended location after the fact.

Modes D1 and D2 allow you to hash, verify, move, delete, and quarantine blobs from the cloud. Modes D1 and D2 only require two arguments, which are --source and --mode "D1"/--mode "D2". Just like mode C, source should be an empty or random string with a space " " since the program does not require a path for modes D1 and D2. To run this, simply enter the following into your terminal:

#### Windows
Run this command: **python main-control.py --source " " --mode "D1"**
#### macOS / Linux
Run this command: **python3 main-control.py --source " " --mode "D1"**

Please follow any input prompts the program may give you. If notifications and webhooks are set up, you will receive notifications and webhooks when your input is needed.

#### MODE D2

**You may also schedule this to occur every day at a specific time, to do this simply swap --mode "D1" for --mode "D2".**

-----------------------------------------------------------------------------------------------
## Miscellaneous
At this stage of the project, I cannot make any promises that all features I intend to add will be able to be done. If this is the case, this ReadMe.md will be updated accordingly. This tool is for diagnostic purposes only and does not provide data recovery services. If data loss or corruption is detected, users should rely on their established backup restoration procedures or professional data recovery services. Thank you! 
### **LAST UPDATED: August 24th, 2026.**