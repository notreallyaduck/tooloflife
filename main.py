import math
import os
import shutil
import stat
import webbrowser
from datetime import datetime
from time import sleep
import exifread
import tkinter as tk
from tkinter import filedialog


def has_hidden_attribute(filepath):
    directory = filepath.split("/")
    file_name = directory[-1]

    try:
        if file_name.startswith("."):
            return True
        elif bool(os.stat(filepath).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) is True:
            print(filepath)
            print(bool(os.stat(filepath).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN))
            return True
    except AttributeError:
        return False


def about():
    print("About this tool"
          "\nThis is a tool designed to help streamline the processes regarding file management within the PSHS "
          "\nMultimedia Team.")
    input("\nPress Enter to go back to the main menu")


def duplicate(output_path, file_path, tag, duplicate_files):
    directory = file_path.split("/")
    file_name = directory[-1]

    if os.path.exists(output_path + "/" + tag + "/" + file_name):
        duplicate_files.append(file_path)
        if not os.path.exists(output_path + "/Duplicates"):
            os.mkdir(output_path + "/Duplicates")
            shutil.copy(file_path, output_path + "/Duplicates")
        else:
            shutil.copy(file_path, output_path + "/Duplicates")


def missing_exif(file_path, output_path, no_exif, movies, media_type):
    if media_type == "Image":
        no_exif.append(file_path)
        if not os.path.exists(output_path + "/Other"):
            os.mkdir(output_path + "/Other")
            shutil.copy(file_path, output_path + "/Other")
        else:
            shutil.copy(file_path, output_path + "/Other")
    if media_type == "Movie":
        movies.append(file_path)
        if not os.path.exists(output_path + "/Videos"):
            os.mkdir(output_path + "/Videos")
            shutil.copy(file_path, output_path + "/Videos")
        else:
            shutil.copy(file_path, output_path + "/Videos")


def camera_dir(output_path, file_path, tag):
    if not os.path.exists(output_path + "/" + tag):
        print("Camera specific folder for " + tag + " does not exist")
        print("Creating one now")
        os.mkdir(output_path + "/" + tag)
        shutil.copy(file_path, output_path + "/" + tag)
    else:
        shutil.copy(file_path, output_path + "/" + tag)


def file_is_media(file_path):
    directory = file_path.split("/")
    file_name = directory[-1]
    file_suffix = file_name.split(".")
    file_type = file_suffix[-1].lower()

    if file_type == "jpg" or file_type == "nef" or file_type == "cr2" or file_type == "dng" \
            or file_type == "jpg" or file_type == "nef" or file_type == "cr2" or file_type == "dng" \
            or file_type == "orf":
        return "Image"
    elif file_type == "avchd" or file_type == "avi" or file_type == "mp4" or file_type == "mov":
        return "Movie"
    else:
        return False


def ingest(ingest_logs, file_list):
    no_exif = []
    movies_list = []
    duplicate_files = []
    file_count = 0
    file_path = []
    processed_files = []
    root_output_dir = "/Users/sudesh/Pictures/Multimedia/"
    ignored_volumes = []
    print("\nIngest mode"
          "\nCurrently attached volumes"
          "\nPlease wait as sizes are calculated. ")

    for entry in os.listdir("/Volumes"):
        volume = os.path.join("/Volumes", entry)
        dir_size = round(shutil.disk_usage(volume).total / 1280000000)
        print(f"- {entry} ({str(dir_size)} gigabytes)")

        if dir_size > 128:
            ignored_volumes.append(entry)
        if entry in ignored_volumes:
            print("  ^ This volume will be ignored")

    print("\nSizes are approximate\n")
    sleep(1)
    event_name = input("What event are these files from?\n> ")
    output_path = root_output_dir + event_name

    if os.path.exists(output_path):
        pass
    else:
        os.mkdir(output_path)

    if os.path.exists("/Volumes/"):
        while True:
            for entry in os.listdir("/Volumes"):
                os.path.join("/Volumes", entry)

                if entry not in ignored_volumes:
                    ingest_path = "/Volumes/" + entry
                    ignored_volumes.append(entry)

                    for root, dirs, files in os.walk(ingest_path):
                        for name in files:
                            file_path.append(os.path.join(root, name))

            print(f"\n{len(file_path)} files to process\n")

            for item in file_path:

                file_type = file_is_media(item)

                processed_files.append(item)
                completion = round(len(processed_files) / len(file_path) * 100)

                print(f"{completion} percent processed")

                if has_hidden_attribute(item) is False and file_type:
                    try:
                        file = open(item, 'rb')
                        tags = exifread.process_file(file, stop_tag='Model')
                        try:
                            tag = str(tags["Image Model"])
                            duplicate(output_path, item, tag, duplicate_files)
                            camera_dir(output_path, item, tag)
                            file_list.append(output_path + "/" + tag + "/" + os.path.basename(item))
                            file_count = file_count + 1
                        except KeyError:
                            tag = "Other"
                            duplicate(output_path, item, tag, duplicate_files)
                            missing_exif(item, output_path, no_exif, movies_list, file_type)
                            file_list.append(output_path + "/" + tag + "/" + os.path.basename(item))
                            file_count = file_count + 1
                    except PermissionError:
                        pass
                    except shutil.Error:
                        pass
                    except TypeError:
                        pass

                elif has_hidden_attribute(item) is True:
                    pass

                elif file_is_media(item) is False:
                    pass

            print("\nIngested " + str(file_count) + " files\n")
            processed_files.clear()

            if len(no_exif) > 0:
                print("These files did not have camera information in their EXIF data: ")
                for i in no_exif:
                    print(i)
                print("They have been placed in a separate folder (Other)\n")

            if len(duplicate_files) > 0:
                print("These files had duplicate filenames: ")
                for i in duplicate_files:
                    print(i)
                print("They have been placed in a separate folder (Duplicates)\n")

            more_files = input("Are there more files to transfer? (Yes/No)"
                               "\nIf you have another storage device, plug it in now.\n")

            if more_files in ["No", "no", "N", "n", "NO", "Nup", "Nah", "nup", "nah"]:
                ingest_logs.append(f"[{str(datetime.today())}]  + {str(file_count)} files ingested")
                no_exif.clear()
                movies_list.clear()
                duplicate_files.clear()
                ignored_volumes.clear()
                processed_files.clear()
                return output_path

            if more_files in ["Yes", "yes", "Y", "y", "YES"]:
                print("Looking for new drives")
                continue

            else:
                print("Type Yes or No")


def delegate(delegate_logs, output):
    available_files = []
    copied_files = []
    files_out = output

    if output:
        print("Would you like to use the files you just ingested or do you want to select a different folder?"
              "\nPress enter to use ingested files or type New to select a new folder")
        new_folder = input()
        if new_folder == "New" or "new" or "n" or "New Folder" or "new folder":
            del output

    while not files_out:
        root = tk.Tk()
        root.withdraw()
        files_out = filedialog.askdirectory()

    for root, dirs, files in os.walk(files_out):
        for name in files:
            if "Delegations" and "Duplicates" not in root:
                file_path = os.path.join(root, name)
                available_files.append(file_path)

    name_input = input("Write the names of each editor separated by a comma. \n"
                       "(Steve, Matt Smith, Pikachu, Robbie, Anne)\n")
    names = name_input.split(",")

    try:
        os.mkdir(files_out + "/Delegations/")
    except FileExistsError:
        pass
    except OSError:
        print("Delegations folder is read only, please check permissions")

    files_len = len(available_files)

    for index, name in enumerate(names):

        name = name.strip()

        each_user = math.ceil(files_len / len(names))
        my_files = []
        files_before = each_user * (index - 1)
        this_editor = []

        for x in range(each_user):
            my_files.append(available_files[files_before + x])

        path = files_out + f"/Delegations/{name}"

        try:
            os.mkdir(path)
        except FileExistsError:
            pass
        except FileNotFoundError:
            print("Folder does not exist")
            return

        for file in my_files:
            print(file)
            if has_hidden_attribute(file) is False and file_is_media(file) is True:
                shutil.copy(file, path)
                this_editor.append(file)
                copied_files.append(file)
            else:
                pass

        delegate_logs.append(f"[{str(datetime.today())}] Files delegated to {len(names)} people")

        print(f"{name} was delegated {len(this_editor)} files in folder {path}\n")


def upload():
    return 0


def todo():
    return 0


def status():
    return 0


def logs(stored_logs):
    print("Operations completed this session:")
    for i in range(0, len(stored_logs)):
        print(stored_logs[i])
    input("\nPress Enter to go back to the main menu")
    return 0


def main():
    stored_logs = []
    path = ""
    app_dir = "/Users/sudesh/Pictures/Multimedia"
    stored_files = []
    print("tooloflife v0.0.1")
    sleep(0.5)
    while True:
        print("\n[0] About"
              "\n[1] Ingest"
              "\n[2] Delegate"
              "\n[3] Logs"
              "\n[4] Open Folder")
        current_menu = input("> ").strip()

        match current_menu:
            case "0":
                continue
            case "1":
                path = ingest(stored_logs, stored_files)
            case "2":
                delegate(stored_logs, path)
            case "3":
                logs(stored_logs)
            case "4":
                webbrowser.open("file:///" + os.path.realpath(app_dir))
            case _:
                print("Select a valid option")


if __name__ == '__main__':
    main()
