# 3-2-1-Sync-Done!
## Project Overview
3-2-1, Sync Done! is a project which was created to demonstrate a practical understanding and tangible demonstration of core data protection strategies. This project is done as a companion to the industry standard 3-2-1 data backup policies, and is directly focused on ensuring data integrity. 3-2-1 Sync Done! utilizes scripts, cloud + local storage, health checks, and storage alerts to ensure these principles are adhered to in a professional manner. This is done to avoid many situations that threaten data integrity including but not limited to hardware failure, bit rot (data degradation), ransomware, file tampering, local and online synchronization failures, software bugs, and human error.

------------------------------------------------------------------------
## Language, Tools, and Frameworks
### Language 
This project is being made with **Python 3.12.1**, and as such uses tools and frameworks connected to Python. 
### Tools
Common tools in use include JavaScript Object Notation (**JSON**) for the manifest, the hashlib library for hashing files in the **SHA-256 (Secure Hash Algorithm 256-bit)** format, and the built-in logging module which directly outputs detailed information to loginfo.log.  It is quite likely that more tools will be used as the project expands in scope, especially when seamless online and local integration is added. 
### Frameworks
To ensure connectivity with a cloud data storage provider, the user will have to verify their credentials through a secure connection, and will be done through some SDK or API. This will be made clear as soon as more information is available.

-----------------------------------------------------------------------------------------------
## How To Run
To run the 3-2-1 Sync Done! application, type the following command into the terminal: **python main-control.py --source "/path/to/data" --source2 "/path/to/data" ** or if you want to only to use the program on files with a specific extension, please use the command **python main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension".** You **must** provide a directory to a **folder**, not a path to a specific file. If this doesn't work, it is likely because of Windows being unable to find where Python is installed on your machine. As such, if Python is installed correctly use this: **/c/Users/YOURUSERNAME/AppData/Local/Programs/Python/Python312/python.exe main-control.py --source "/path/to/data" --source2 "/path/to/data" --ext "extension"**. Please note, that --source2 and --ext are optional, while --source1 is required.

-----------------------------------------------------------------------------------------------
## Miscellaneous
At this stage of the project, I cannot make any promises that all features I intend to add will be able to be done. If this is the case, this ReadMe.md will be updated accordingly. Also, please note, due to the sensitive nature of data, I do not have the capability to retrieve any lost, corrupted, or tampered data. As such, if something does go wrong in regards to the data itself, you should reach out to dedicated data recovery specialists or your cloud storage provider directly. Thank you! 
### **LAST UPDATED: July 12th, 2026.**


