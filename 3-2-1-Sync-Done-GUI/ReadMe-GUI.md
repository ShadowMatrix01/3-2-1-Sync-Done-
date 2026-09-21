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

AZURE_CONTAINER_TARGET=YOUR_TARGET_CONTAINER_TO_COPY_TO

AZURE_CONTAINER_QUARANTINE=YOUR_AZURE_QUARANTINE_CONTAINER_NAME

TIME_IN_24_HOURS_LOCAL=HH:MM

TIME_IN_24_HOURS_CLOUD=HH:MM

TIMEZONE_DST_AWARE=YOUR_TIMEZONE

**VirusTotal API DISCLAIMER:** This project includes optional integration with the VirusTotal API. This tool is a file integrity auditor. It is **not** an antivirus. It does not actively monitor your computer for viruses, and is only allowed to move files to a "quarantine" folder. This is due to VirusTotal's Terms of Service; as such, please keep this in mind. Usage of this feature is entirely at the user's discretion and is subject to VirusTotal's Terms of Service. The developer of this tool assumes no liability for the user's compliance with these terms or for the API's rate-limiting policies.

**You must supply your own VirusTotal key in your own .env file.**

Ensure the VirusTotal API is working by using Mode C and selecting the VirusTotal API Check.

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
8. Ensure the webhook is working by using Mode C and selecting the Discord Webhook Integration Check.
9. After verification is successful, you are done!

**Azure Storage Blobs Setup**

After creating your Azure account and your Azure Blob Storage Account, please follow these steps:

1. Log in to the Azure portal and navigate to your storage account.
2. On the left-hand menu, click Access Keys (under Security + networking).
3. Copy the connection string under key1.
4. Put this connection string in the .env file as AZURE_CONNECT_STR=YOUR_AZURE_CONNECTION_STRING.
5. Go to containers under data storage in your storage account and create two private containers.
6. Once you have these two containers, put the source container with the blobs in the .env file as AZURE_CONTAINER=YOUR_AZURE_CONTAINER_NAME, and the container for quarantining and logging as AZURE_CONTAINER_QUARANTINE=YOUR_AZURE_QUARANTINE_CONTAINER_NAME.

-----------------------------------------------------------------------------------------------

### Language
This project is being made with **Python 3.12.1**, and as such uses tools and frameworks connected to Python.
### Tools
Common tools in use include JavaScript Object Notation (**JSON**) for the manifest, the hashlib library for hashing files in the **SHA-256 (Secure Hash Algorithm 256-bit)** format, shutil for moving files to quarantine, stat for getting a files metdatata, and the built-in logging module which directly outputs detailed information to loginfo.log.
### Frameworks/API/SDK/Other
Plyer 2.1.0 and discord-webhook 1.4.1 are libraries added to handle corrupted, tampered, and potentially malicious files. This ensures the user is notified not only immediately within the program, but also via desktop notifications and multiple devices simultaneously through Discord webhooks. This gives the user a detailed log to reference later if new or unusual behaviors are detected in a file or blob, and it ensures the user's attention is immediately grabbed when a file is under review by the program.

Please note, Discord webhooks require a free Discord account. For more information, please click here: https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

Chime 0.8.0 is a simple auditory cue system that is cross-compatible across different operating systems. This was added because sounds are not included with plyer, and I felt that auditory cues are needed. For more information, please visit: https://pypi.org/project/chime/

Schedule 1.2.2 runs Python functions (or any other callable) periodically using a friendly syntax. It utilizes a simple-to-use API for scheduling jobs, has an in-process scheduler for periodic jobs, and is lightweight with no external dependencies. It is tested to run on Python 3.7, 3.8, 3.9, 3.10, 3.11, and 3.12. Schedule 1.2.2 uses the 24-hour clock, with the format HH:MM. For more information, please visit: https://pypi.org/project/schedule/

Pytz-2026.3.post1 brings the Olson tz database into Python. This library enables accurate, cross-platform timezone calculations in Python 2.4 or higher. Almost all the Olson time zones are supported. It also solves the issue of ambiguous times at the end of daylight saving time. In this application, I am using it in conjunction with schedule 1.2.2 to ensure that the program can run by itself on a daily basis. My program supports 594 pytz time zones, which can be found in the pytz_timezones.txt file. For more information, please visit: https://pypi.org/project/pytz/

Microsoft Azure Blob Storage SDK (azure-core 1.41.0 and azure-storage-blob 12.30.0) is used for the application's cloud features. Azure Blob Storage uses data lakes, machine learning, and scalable technologies to ensure optimal performance with stored blobs. My application allows blobs (unstructured cloud files) to be hashed directly within the application. In addition to this, the 3-2-1-Sync-Done! application allows the same functionality present in the local version (hashing, scanning, moving, quarantining, logging, etc.) to be used with the cloud version. To utilize this, you **must** ensure that you have both a free Azure account and an Azure Blob Storage Account. In this account, you must have at least two containers; one of these is a normal container where blobs (files) will be stored. The other is the quarantine container, which is where potentially malicious blobs will be moved to with a corresponding log. You **must** ensure that these are put in the corresponding fields in the .env file, as mixing them up will result in normal blobs and potentially malicious blobs being put in the wrong place.

Pillow 12.3.0 is a Python Imaging Library (Fork). The Python Imaging Library adds image processing capabilities to your Python interpreter. This library provides extensive file format support, an efficient internal representation, and fairly powerful image processing capabilities. The core image library is designed for fast access to data stored in a few basic pixel formats. It should provide a solid foundation for a general image processing tool.

For more information on Pillow, please visit: https://pypi.org/project/pillow/

Customtkinter 6.0.0 is a modern and customizable python UI-library based on Tkinter. CustomTkinter is a python desktop UI-library based on Tkinter, which provides modern looking and fully customizable widgets. With CustomTkinter you'll get a consistent look across all desktop platforms (Windows, macOS, Linux). For more information, please visit: https://customtkinter.tomschimansky.com/documentation/

-----------------------------------------------------------------------------------------------

## How To Run

The application is now run through the graphical user interface. Select the desired mode from the main menu and follow the prompts provided by the application.

### Hashing Files and Checking Integrity of Files, MODES A1 and A2.

Modes A1 and A2 are used for hashing files and checking the integrity of files.

For Mode A1, select Mode A1 from the main menu and select the directory you want to hash. You **must** provide a directory path, not a specific file path. You may also specify a second directory and a file extension when prompted.

**MODE A2**

You may also schedule this to occur every day at a specific time by selecting Mode A2. The application will use the schedule and timezone preferences configured in the application.

### Checking the integrity of a specific file in a specific manifest, MODES: 1B and 2B.

Modes 1B and 2B are used to quickly check the integrity of a specific file.

1. First, select the specific **FILE** you want to verify. If you supply a directory, it will always fail. This is intentional. Modes A1 and A2 should be used for a complete hashing and verification of a directory, whereas modes 1B and 2B should be used for quickly checking the integrity of a specific file.

2. Do **NOT** include a second source or file extension. These modes are intended to check a specific file.

3. To check for the file in manifest.json, use Mode 1B. Otherwise, to check for the file in manifest2.json, use Mode 2B.

4. If you see something odd or suspicious, **do NOT overwrite your manifests or delete them**. Instead, manually check the file in question.

5. Improperly formatted JSON will result in the program throwing errors. It is wise not to manually modify the manifest files, and instead copy them and place them somewhere secure, before creating new manifests.

### Check if Local Notifications, Discord Webhook, Azure Storage Blobs, VirusTotal API are working as intended, Set Alert and Schedule Preferences, and Set Time and Timezone for Schedule, MODE C.

Mode C allows you to check before running the program if everything is set up correctly.

From the main menu, select Mode C. From there, you will be prompted to select an option from a menu.

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

Modes D1 and D2 allow you to hash, verify, move, delete, and quarantine blobs from the cloud.

Select Mode D1 from the main menu and follow any input prompts the program may give you. If notifications and webhooks are set up, you will receive notifications and webhooks when your input is needed.

**MODE D2**

You may also schedule this to occur every day at a specific time by selecting Mode D2. The application will use the schedule and timezone preferences configured in the application.

### Copy Files From The Manifests To Directory/Container, MODES E1, E2, AND E3.

After some files have been hashed to the manifests, you may want to make a copy of such files to another directory or container. This allows verified and stable backups, which fully complete the mission of this project.

## Copy Files From manifest.json/manifest2.json to another directory, MODES E1 and E2.

Please note, the program is currently setup to **not** copy files older than a week. This is likely to change, depending on what I and other test users feel is an ideal timeframe, as product testing is set to commence soon.

To copy files from manifest.json to a directory, select Mode E1 and make the **target** directory the directory selected in the application. You **must** hash a file in the program before copying it, this is for security and stability reasons.

**MODE E2**

If you wish to move files from manifest2.json, select Mode E2.

## Copy Azure Blobs From One Container to Another Container, MODE E3.

Unlike Modes E1 and E2, there is no need to supply a directory. **However, you must check that the AZURE_CONTAINER_TARGET value in the .env file is correct**. If not, the program will run, but will copy blobs to the wrong container, which is not ideal.

After verifying this, select Mode E3 to copy blobs from manifest_cloud.json to the target container.

-----------------------------------------------------------------------------------------------

## Miscellaneous
At this stage of the project, I cannot make any promises that all features I intend to add will be able to be done. If this is the case, this ReadMe.md will be updated accordingly. This tool is for diagnostic purposes only and does not provide data recovery services. If data loss or corruption is detected, users should rely on their established backup restoration procedures or professional data recovery services. Thank you!

### **LAST UPDATED: September 21st, 2026.**