# 3-2-1-Sync-Done!
## Project Overview
3-2-1, Sync Done! Demonstrates core data protection strategies in a practical way. It is a companion to the industry standard 3-2-1 data backup policy and focuses on data integrity. The project uses scripts, cloud and local storage, health checks, and storage alerts to support these principles and help prevent hardware failure, bit rot, ransomware, file tampering, synchronization failures, software bugs, and human error.

------------------------------------------------------------------------------------------------
### Language 
This project is being made with **Python 3.12.1**, and as such uses tools and frameworks connected to Python. 
### Tools
Common tools in use include JavaScript Object Notation (**JSON**) for the manifest, the hashlib library for hashing files in the **SHA-256 (Secure Hash Algorithm 256-bit)** format, and the built-in logging module which directly outputs detailed information to loginfo.log.  It is quite likely that more tools will be used as the project expands in scope, especially when seamless online and local integration is added. 
### Frameworks
To ensure connectivity with a cloud data storage provider, the user will have to verify their credentials through a secure connection, and will be done through some SDK or API. This will be made clear as soon as more information is available.

-----------------------------------------------------------------------------------------------
## How To Run

### Hashing Files

#### Windows

To run the 3-2-1 Sync Done! application for hashing files, type the following command into the terminal: **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --mode "A".** If you want to use the program only on files with a specific extension, use: **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".** You **must** provide a directory path, not a specific file path. If this does not work, it is likely because Windows cannot find where Python is installed on your machine. If Python is installed correctly, use this instead: **/c/Users/YOURUSERNAME/AppData/Local/Programs/Python/Python312/python.exe main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".** Please note that --source2 and --ext are optional, while --source and --mode are **required**. You may also be able to run it through cmd as **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".**

#### macOS / Linux

To run the 3-2-1 Sync Done! application for hashing files on macOS or Linux, type the following command into the terminal: **python3 main-control.py --source "/path/to/data" --source2 "/path/to/data" --mode "A".** If you want to use the program only on files with a specific extension, use: **python3 main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension" --mode "A".** You **must** provide a directory path, not a specific file path. On most macOS and Linux systems, python3 is the correct command. If python3 does not work, try replacing it with python. Please note that --source2 and --ext are optional, while --source and --mode are **required**.

### Checking the integrity of a specific file in a specific manifest

To run the 3-2-1 Sync Done! application to verify the integrity of a specific file, you must note the following.

1. First, you must get the specific path to the **FILE** you want to verify. If you supply a directory, such as C:\Users\YOURUSERNAME, it will always fail. The correct usage would be C:\Users\YOURUSERNAME\file.txt on Windows or /home/YOURUSERNAME/file.txt (Linux) or /Users/YOURUSERNAME/file.txt (macOS). This is intentional. Mode A should be used for a complete hashing and verification of a directory, whereas modes 1B and 2B should be used for quickly checking the integrity of a specific file.

2. **Do NOT include --source2 or --ext.** If you do, the program will not work. Instead follow step 3.

3. To check for the file in manifest.json, please use --mode "1B". Otherwise, to check for the file in manifest2.json, please use --mode "2B". 

4. If you see something odd or suspicious, **do NOT overwrite your manifests or delete them**. Instead, manually check the file in question.

5. Improperly formatted JSON will result in the program throwing errors. It is wise to not manually modify the manifest files, and instead copy them and place them somewhere secure, before creating new manifests.

-----------------------------------------------------------------------------------------------
## Miscellaneous
At this stage of the project, I cannot make any promises that all features I intend to add will be able to be done. If this is the case, this ReadMe.md will be updated accordingly. Also, please note, due to the sensitive nature of data, I do not have the capability to retrieve any lost, corrupted, or tampered data. As such, if something does go wrong in regards to the data itself, you should reach out to dedicated data recovery specialists or your cloud storage provider directly. Thank you! 
### **LAST UPDATED: July 17th, 2026.**