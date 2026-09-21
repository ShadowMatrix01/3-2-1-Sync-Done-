import os
import logging
import json
import shutil
import ijson
import customtkinter as ctk
from tkinter import filedialog
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import HttpResponseError
load_dotenv()
def create_manifest(path):
    with open(path, "w") as f_create:
         json.dump({}, f_create)
def inner_validate(app, file):
    if not os.path.exists(f'{file}.json') or os.path.getsize(f"{file}.json") == 0: 
       create_manifest(f"{file}.json")
    try:
        with open(f'{file}.json', 'r') as valid:
             json.load(valid)
    except ijson.common.IncompleteJSONError:
            logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
            app.write_box(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
            app.write_box("This program will exit in 5 seconds for security reasons.")
            return
    except Exception:
             logging.basicConfig(level=logging.INFO, filename="loginfo.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
             app.write_box(f"ERROR! The manifest file {file} is corrupted. You must manually check it, as the program will not run to avoid overwriting this data.")
             app.write_box("This program will exit in 5 seconds for security reasons.")
             return
def mover_helper(app, directory_2, manifest_2):
    global inner
    global break_outer
    global switch_dir
    inner = False
    break_outer = False
    switch_dir = False
    app.write_box(f"Program restarting for directory {directory_2}.")
    mover(app, directory_2, manifest_2)
def disk_space_choice(app, file):
    choice = {"value": "exit"}
    window = ctk.CTkToplevel(app)
    window.title("Insufficient Disk Space")
    window.geometry("500x300")
    window.resizable(False, False)
    window.grab_set()
    file_name = Path(file).name
    if len(file_name) > 40:
        file_name = file_name[:37] + "..."
    copy_option = f"Copy all files before {file_name}"
    label = ctk.CTkLabel(
        window,
        text=f"Not enough space to copy {file_name}.\nPlease select an option:"
    )
    label.grid(row=0, column=0, padx=10, pady=20)
    dropdown = ctk.CTkOptionMenu(
        window,
        values=[
            copy_option,
            "Specify a new directory",
            "Exit"
        ],
        width=300
    )
    dropdown.grid(row=1, column=0, padx=10, pady=10)
    window.grid_columnconfigure(0, weight=1)
    dropdown.set(copy_option)
    def close_window(value="exit"):
        choice["value"] = value
        window.destroy()
    def confirm():
        selected = dropdown.get()
        if selected == copy_option:
            close_window("copy_before")
        elif selected == "Specify a new directory":
            close_window("Specify a new directory")
        else:
            close_window("Exit")
    button = ctk.CTkButton(
        window,
        text="Confirm",
        command=confirm
    )
    button.grid(row=2, column=0, padx=10, pady=20)
    def quit_app():
        window.destroy()
        app.destroy()
    window.protocol("WM_DELETE_WINDOW", quit_app)
    app.wait_window(window)
    return choice["value"]
def select_files(app, arr, title, item_type):
    selected = []
    window = ctk.CTkToplevel(app)
    window.title(title)
    window.geometry("500x500")
    window.resizable(False, False)
    label = ctk.CTkLabel(
        window,
        text=f"Please select the {item_type} you would like to copy:"
    )
    label.grid(row=0, column=0, padx=10, pady=10)
    scroll_frame = ctk.CTkScrollableFrame(
        window,
        width=450,
        height=350
    )
    scroll_frame.grid(
        row=1,
        column=0,
        padx=10,
        pady=10,
        sticky="nsew"
    )
    checkboxes = []
    for index, item in enumerate(arr):
        checkbox = ctk.CTkCheckBox(
            scroll_frame,
            text=item
        )
        checkbox.grid(
            row=index,
            column=0,
            padx=10,
            pady=5,
            sticky="w"
        )
        checkboxes.append((item, checkbox))
    def confirm():
        selected.clear()
        for item, checkbox in checkboxes:
            if checkbox.get() == 1:
                selected.append(item)
        window.destroy()
    button = ctk.CTkButton(
        window,
        text="Confirm Selection",
        command=confirm
    )
    button.grid(row=2, column=0, padx=10, pady=10)
    scroll_frame.grid_columnconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)
    window.grid_rowconfigure(1, weight=1)
    window.protocol("WM_DELETE_WINDOW", window.destroy)
    app.wait_window(window)
    return selected
def move_choice(app, item_type):
    choice = {"value": None}
    window = ctk.CTkToplevel(app)
    window.title("Move Options")
    window.geometry("450x250")
    window.resizable(False, False)
    window.grab_set()
    label = ctk.CTkLabel(
        window,
        text=f"What would you like to do with the {item_type}?"
    )
    label.grid(row=0, column=0, padx=10, pady=10)
    dropdown = ctk.CTkOptionMenu(
        window,
        values=[
            f"Copy All {item_type}",
            f"Manually Select {item_type}",
            "Nothing, exit"
        ],
        width=300
    )
    dropdown.grid(row=1, column=0, padx=10, pady=10)
    dropdown.set(f"Copy All {item_type}")
    def confirm():
        choice["value"] = dropdown.get()
        window.destroy()
    button = ctk.CTkButton(
        window,
        text="Confirm",
        command=confirm
    )
    button.grid(row=2, column=0, padx=10, pady=20)
    window.protocol("WM_DELETE_WINDOW", window.destroy)
    app.wait_window(window)
    return choice["value"]
def mover(app, directory, manifest):
     global inner
     global break_outer
     logging.basicConfig(level=logging.INFO, filename=f"{manifest}.log", format='%(asctime)s - %(levelname)s: %(message)s', force=True)
     file_dir = Path(directory)
     dir_size = 0
     move_count = 0
     if file_dir.is_dir():
        disk_total = shutil.disk_usage(file_dir)
        dir_size = disk_total.free
     else:
        app.write_box(f"The directory {file_dir} does not exist.\nThe program will now exit in 5 seconds.")
        return
     arr = []
     failed_arr = []
     total_size = 0
     break_outer = False
     #only valid options will be shown, so if not modified then it will show up in the array, otherwise it will be labeled as Not Available: File
     try:
        try:
            if os.path.getsize(f'{manifest}.json') == 0:
               app.write_box(f"The program cannot run, as there are no entries in {manifest}.json. \nThe program will now exit in 5 seconds.")
               return
            with open(f'{manifest}.json') as f:
                  entries = json.load(f)
            if len(entries) == 0:
               app.write_box("The program cannot run, as there are no entries in manifest_cloud.json. \nThe program will now exit in 5 seconds.")
               return 
        except FileNotFoundError:
               app.write_box("The manifest could not be found by the program. The program will create a new one, and exit in 5 seconds.")
               inner_validate(app, manifest)
               return
        except json.JSONDecodeError:
               logging.critical(f"The manifest file {manifest}.json is corrupted, and as such, the program will not move files for security reasons!")
               app.write_box(f"The {manifest} file {manifest}.json is corrupted, and as such, the program will not move files for security reasons!\nThe program will now exit in 5 seconds.")
               return
        app.write_box(f"Please wait while the program checks the feasibility of moving files from the manifest {manifest}.json to the directory {file_dir}")
        progress = app.progress_bar
        for index, (key, val) in enumerate(entries.items(), start=1):
            if break_outer:
               break
            date = val.get("last_seen", "never")
            file_size = val.get("size", "-1")
            if not date or date == "never" or not file_size or file_size == "-1":
               app.write_box(f"The file {key} is missing its date/size attribute, skipping.")
               continue
            date_convert = datetime.fromisoformat(date)
            cur_date = datetime.now()
            delta = cur_date - date_convert
            delta_2 = delta.days
            if delta_2 <= 7:
               arr.append(key)
               total_size += int(file_size)
               if total_size > dir_size:
                  inner = True
                  while inner:
                     app.write_box(f"Error! There is not enough space to move any more files, including {key} to the directory {file_dir}. ")
                     app.write_box(f"Total size of files in {manifest}.json (up to this point): {total_size}.\nFree space available on disk: {dir_size}.")
                     mv_file = disk_space_choice(app, key)
                     if mv_file == "copy_before":
                        arr.remove(key)
                        total_size -= int(file_size) 
                        if len(arr) == 0:
                           return
                        break_outer = True
                        inner = False
                     elif mv_file == "Specify a new directory":
                        directory_change = filedialog.askdirectory(
                        title="Select a directory"
                        )
                        if not directory_change:
                           app.write_box("Directory selection cancelled.")
                           return
                        mover_helper(app, directory_change, manifest)
                        return
                     elif mv_file == "Exit":
                        return
            progress.set(index / len(entries))
            app.update_idletasks()
        progress.set(0)
        move_op = move_choice(app, "Files")
        if move_op == "Copy All Files":
            pass
        elif move_op == "Manually Select Files":
            arr = select_files(
               app,
               arr,
               "Select Files", "files"
            )
        else:
            app.write_box("File copying cancelled.")
            return
        app.write_box(f"Please wait while the program copies the files over to the directory {file_dir}")
        if len(arr) == 0:
           return
        progress = app.progress_bar
        for index, value in enumerate(arr, start=1):
            #Added because some files are way too long to show.
            file_name = Path(value).name
            if len(file_name) > 40:
                file_name = file_name[:37] + "..."
            app.progress_label.configure(
                text=f"Copying file: {file_name} to {file_dir}..."
            )
            file_path = Path(value)
            if file_path.is_file():
               try:
                  shutil.copy2(value, file_dir)
                  move_count = move_count + 1
               except PermissionError:
                  app.write_box(f"FAILURE: Program lacks permissions to copy the file {file_path} to {file_dir}. Aborting copy.")
                  logging.critical(f"FAILURE: Program lacks permissions to copy the file {file_path} to {file_dir}. Aborting copy.")
                  failed_arr.append(value)
               except shutil.Error as e:
                  app.write_box(f"ERROR: {e}")
                  logging.critical(f"ERROR with moving {file_path} to directory {file_dir}: {e}")
                  failed_arr.append(value)    
               except OSError as e: 
                  app.write_box(f"ERROR: {e}") 
                  logging.critical(f"ERROR with moving {file_path} to directory {file_dir}: {e}")   
                  failed_arr.append(value) 
            else:
               app.write_box(f"This file {value} does not exist on the disk. Aborting move")
               logging.warning(f"This file {value} does not exist on the disk. Aborting move")
               failed_arr.append(value)    
            progress.set(index / len(arr))
            app.update_idletasks()
        progress.set(0)    
     except Exception as e:
        app.write_box(f"Exception: {e}")
     logging.info(f"Successfully moved {move_count} entries to directory {file_dir}.")
     return  
def mover_2(app):
    total_size = 0
    move_count = 0
    arr = []
    failed_arr = []
    azure_connection_string = os.getenv("AZURE_CONNECT_STR")
    azure_container_source = os.getenv("AZURE_CONTAINER")
    azure_container_target = os.getenv("AZURE_CONTAINER_TARGET")
    if not azure_connection_string :
       app.write_box("Error: AZURE_CONNECT_STR not found. Please create a .env file based on .env example")
       return
    if not azure_container_source:
       app.write_box("Error: AZURE_CONTAINER not found. Please create a .env file based on .env example")
       return
    if not azure_container_target:
        app.write_box("Error: AZURE_CONTAINER_TARGET not found. Please create a .env file based on .env example")
        return
    try:
        if os.path.getsize('manifest_cloud.json') == 0:
           app.write_box("The program cannot run, as there are no entries in manifest_cloud.json. \nThe program will now exit in 5 seconds.")
           return
        with open('manifest_cloud.json') as f:
             entries = json.load(f)
        if len(entries) == 0:
           app.write_box("The program cannot run, as there are no entries in manifest_cloud.json. \nThe program will now exit in 5 seconds.")
           return 
    except FileNotFoundError:
           app.write_box("The manifest could not be found by the program. The program will create a new one, and exit in 5 seconds.")
           inner_validate(app, "manifest_cloud")
           return
    except json.JSONDecodeError:
           logging.critical("The manifest file manifest_cloud.json is corrupted, and as such, the program will not move blobs for security reasons!")
           app.write_box("The manifest file manifest_cloud.json is corrupted, and as such, the program will not move blobs for security reasons!\nThe program will now exit in 5 seconds.")
           return
    app.write_box(f"Please wait while the program checks the feasibility of moving blobs from {azure_container_source} to the container {azure_container_target}")
    progress = app.progress_bar
    for index, (key, val) in enumerate(entries.items(), start=1):
            date = val.get("last_seen", "never")
            file_size = val.get("size", "-1")
            if not date or date == "never" or not file_size or file_size == "-1":
               app.write_box(f"The file {key} is missing its date/size attribute, skipping.")
               continue
            date_convert = datetime.fromisoformat(date)
            cur_date = datetime.now()
            delta = cur_date - date_convert
            delta_2 = delta.days
            if delta_2 <= 7:
               arr.append(key)
               total_size += int(file_size)
            progress.set(index / len(entries))
            app.update_idletasks()
    progress.set(0)
    move_op = move_choice(app, "Blobs")
    if move_op == "Copy All Blobs":
      pass
    elif move_op == "Manually Select Blobs":
      arr = select_files(
         app,
         arr,
         "Select Blobs", "blobs"
      )
    else:
      app.write_box("Blob copying cancelled.")
      return
    if len(arr) == 0:
       return
    progress = app.progress_bar
    for index, blob_name in enumerate(arr, start=1):
         #Once again, done because the blobs would be too long to show.
         blob_display = blob_name
         if len(blob_display) > 40:
            blob_display = blob_display[:37] + "..."
         app.progress_label.configure(
             text=f"Copying blob: {blob_display} to {azure_container_target}..."
         )
         try:
               blob_service_client = BlobServiceClient.from_connection_string(azure_connection_string)
               source = blob_service_client.get_blob_client(container=azure_container_source, blob=blob_name)
               if source.exists():
                  target_blob = blob_service_client.get_blob_client(container=azure_container_target, blob=blob_name)
                  target_blob.start_copy_from_url(source.url) 
                  move_count = move_count + 1
               else:
                  app.write_box("This blob does not exist or has been moved, skipping")
                  failed_arr.append(blob_name)
                  continue
         except HttpResponseError as e:
               app.write_box(f"Azure Container Error: {e.status_code}: {e.message}")
               logging.error(f"Azure Container Error: {e.status_code}: {e}")
               failed_arr.append(blob_name)
         except Exception as e:
               app.write_box(f"Unexpected Azure Error: {e}")
               logging.error(f"Unexpected Azure Error: {e}")
               failed_arr.append(blob_name)
         progress.set(index / len(arr))
         app.update_idletasks()
    progress.set(0)
    logging.info(f"Successfully moved {move_count} blobs from container {azure_container_source} to container {azure_container_target}.")
    return
#https://pypi.org/project/discord-webhook/
#https://pypi.org/project/plyer/
#https://pypi.org/project/chime/