import os
import shutil
import stat
from datetime import datetime
from time import sleep
import exifread


def has_hidden_attribute(filepath):
    try:
        return bool(os.stat(filepath).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
    except AttributeError:
        return False


def about():
    print("About this tool"
          "\nThis is a tool designed to help streamline the processes regarding file management within the PSHS "
          "\nMultimedia Team.")
    input("\nPress Enter to go back to the main menu")


def uniquify(output_path, filename, ingest_path, file_path, tags):
    if os.path.exists(output_path + "/" + str(tags["Image Model"]) + "/" + filename):
        print("Duplicate file names detected")
        while os.path.exists(output_path + "/" + str(tags["Image Model"]) + "/" + filename):
            # i += 1
            name = file_path.split(".")
            os.rename(file_path, ingest_path + "/" + name[1] + "i" + "." + name[2])


def missing_exif(file_path, output_path, no_exif):
    no_exif.append(file_path)
    if not os.path.exists(output_path + "/Other"):
        os.mkdir(output_path + "/Other")
        shutil.copy(file_path, output_path + "/Other")
    else:
        shutil.copy(file_path, output_path + "/Other")


def camera_dir(output_path, file_path, tags, file_count):
    if not os.path.exists(output_path + "/" + str(tags["Image Model"])):
        print(tags["Image Model"])
        print("Camera specific folder does not exist")
        print("Creating one now")
        os.mkdir(output_path + "/" + str(tags["Image Model"]))
    else:
        shutil.copy(file_path, output_path + "/" + str(tags["Image Model"]))
    return 1


def file_is_media(file_path):
    if file_path.endswith(".JPG") or file_path.endswith(".jpg") \
            or file_path.endswith(".NEF") or file_path.endswith(".CR2") \
            or file_path.endswith(".dng") or file_path.endswith(".CR3") \
            or file_path.endswith(".AVCHD") or file_path.endswith(".avi") \
            or file_path.endswith(".mp4") or file_path.endswith(".mov"):
        return True
    else:
        return False


def ingest(ingest_logs, file_list):
    no_exif = []
    file_count = 0
    root_output_dir = "/Users/sudesh/Pictures/Multimedia/"
    ignored_volumes = ["Macintosh HD", ".timemachine", "com.apple.TimeMachine.localsnapshots"]
    print("\nIngest mode"
          "\nCurrently attached volumes")
    for entry in os.listdir("/Volumes"):
        os.path.join("/Volumes", entry)
        print("- " + entry)
        if entry in ignored_volumes:
            print("  ^ This volume will be ignored")
    sleep(1)
    event_name = input("What event are these files from?\n> ")
    output_path = root_output_dir + event_name
    if os.path.exists(output_path):
        print("Path already exists (No changes made)")
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

                            file_path = os.path.join(root, name)

                            if file_is_media(file_path) and has_hidden_attribute(file_path) is False:
                                file = open(file_path, 'rb')
                                tags = exifread.process_file(file, stop_tag='Model')

                                try:
                                    tags["Image Model"]
                                except KeyError:
                                    if file_is_media(file_path):
                                        missing_exif(file_path, output_path, no_exif)
                                        file_list.append(output_path + "/Other/" +
                                                         os.path.basename(file_path))
                                except PermissionError:
                                    if file_is_media(file_path):
                                        print("File skipped due to permission error")
                                except shutil.Error:
                                    if file_is_media(file_path):
                                        print("File skipped due to duplication error")
                                else:
                                    file_count = file_count + camera_dir(output_path, file_path, tags, file_count)
                                    file_list.append(output_path + "/" + str(tags["Image Model"]) + "/" +
                                                     os.path.basename(file_path))

                            else:
                                print("Cannot ingest this file (Invalid file type): " + file_path)

            print("\nFiles ingested: " + str(file_count) + "\n")
            print("These files did not have camera information in their EXIF data: ")
            for i in range(0, len(no_exif)):
                print(no_exif[i])
            print("They have been placed in a separate folder (Other)\n")

            more_files = input("Are there more files to transfer? (Yes/No)"
                               "\nIf you have another storage device, plug it in now.\n")
            if more_files in ["No", "no", "N", "n", "NO"]:
                ingest_logs.append("[" + str(datetime.today()) + "] " + " files ingested")
                return output_path
            if more_files in ["Yes", "yes", "Y", "y", "YES"]:
                print("Looking for new drives")
                continue
            else:
                print("Type Yes or No")


def delegate(available_files, output):
    name_input = input("Write the names of each editor separated by a comma. \n"
                       "(Steve, Matt Smith, Pikachu, Robbie, Anne)\n")
    names = name_input.split(",")
    print(output)

    for x in range(len(names)):
        try:
            for i in range(len(names)):
                for f in range(round(len(available_files)/len(names))):
                    if not os.path.exists(output + "/" + names[i].strip()):
                        print("Directory for " + names[i].strip())
                        os.mkdir(output + "/" + names[i].strip())
                        shutil.copy(available_files[f], output + "/" + names[i].strip())
                    else:
                        shutil.copy(available_files[f], output + "/" + names[i].strip())
        except FileNotFoundError:
            print("File not found error: " + available_files[f])


def upload():
    return 0


def print_menu(menu):
    print("\n[0] About"
          "\n[1] Ingest"
          "\n[2] Delegate"
          "\n[3] Upload"
          "\n[4] Todo"
          "\n[5] Status"
          "\n[6] Logs")
    selected_option = input("> ")
    while True:
        match selected_option:
            case "0":
                # About
                return 1
            case "1":
                return 2
            case "2":
                # Delegate
                return 3
            case "3":
                # Upload
                return 4
            case "4":
                # Todo
                return 5
            case "5":
                # Status
                return 6
            case "6":
                # Logs
                return 7
            case _:
                print("Pick an option")
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
    current_menu = 0
    path = ""
    stored_files = []
    print("tooloflife v0.0.1")
    sleep(0.5)
    while True:
        match current_menu:
            case 0:
                current_menu = print_menu(current_menu)
            case 1:
                about()
                current_menu = 0
            case 2:
                path = ingest(stored_logs, stored_files)
                current_menu = 0
            case 3:
                delegate(stored_files, path)
                current_menu = 0
            case 4:
                upload()
                current_menu = 0
            case 5:
                todo()
                current_menu = 0
            case 6:
                status()
                current_menu = 0
            case 7:
                logs(stored_logs)
                current_menu = 0



if __name__ == '__main__':
    main()
