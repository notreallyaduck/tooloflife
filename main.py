import math
import os
import shutil
import stat
import string
import webbrowser
from datetime import datetime
from time import sleep
import exifread
import tkinter as tk
from tkinter import filedialog
import ctypes
import configparser


def write(config_file):
    with open('config.conf', 'w') as configfile:
        config_file.write(configfile)


def get_drives():
    drives = []

    if os.name == "nt":
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(letter + ":\\")
            bitmask >>= 1
    elif os.name == "posix":
        for entry in os.listdir("/Volumes"):
            volume = os.path.join("/Volumes", entry)
            drives.append(volume)

    return drives


def has_hidden_attribute(filepath, file_name):

    if file_name.startswith('.'):
        return True
    else:
        try:
            return bool(os.stat(filepath).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
        except AttributeError:
            return False


def about():
    print('About this tool'
          '\nThis is a tool designed to help streamline the processes regarding file management within the PSHS '
          '\nMultimedia Team.'
          '\n\nSudesh Arunachalam sends his highest regards on the survival of anyone who uses this piece of software.')
    input('\nPress Enter to go back to the main menu')


def duplicate(output_path, file_path, tag, duplicate_files, file_name):
    if os.path.exists(output_path + '/' + tag + '/' + file_name):
        duplicate_files.append(file_path)

        if not os.path.exists(output_path + '/Duplicates'):
            os.mkdir(output_path + '/Duplicates')
            shutil.copy(file_path, output_path + '/Duplicates')

        else:
            shutil.copy(file_path, output_path + '/Duplicates')


def missing_exif(file_path, output_path, no_exif, movies, media_type):
    if media_type == 'Image':
        no_exif.append(file_path)

        if not os.path.exists(output_path + '/Other'):
            os.mkdir(output_path + '/Other')
            shutil.copy(file_path, output_path + '/Other')

        else:
            shutil.copy(file_path, output_path + '/Other')

    if media_type == 'Movie':
        movies.append(file_path)

        if not os.path.exists(output_path + '/Videos'):
            os.mkdir(output_path + '/Videos')
            shutil.copy(file_path, output_path + '/Videos')

        else:
            try:
                shutil.copy(file_path, output_path + '/Videos')
            except OSError:
                print("Something went wrong: " + file_path)


def camera_dir(output_path, file_path, tag):
    if not os.path.exists(output_path + '/' + tag):
        print('Camera specific folder for ' + tag + ' does not exist')
        print('Creating one now')
        os.mkdir(output_path + '/' + tag)
        shutil.copy(file_path, output_path + '/' + tag)

    else:
        shutil.copy(file_path, output_path + '/' + tag)


def file_is_media(file_path):
    image_extensions = ('3fr', 'ari', 'arw', 'bay', 'braw', 'crw', 'cr2', 'cr3', 'cap', 'data', 'dcs', 'dcr', 'dng',
                        'drf', 'eip', 'erf', 'fff', 'gpr', 'iiq', 'k25', 'kdc', 'mdc', 'mdc', 'mef', 'mos', 'mrw',
                        'nef', 'nrw', 'obm', 'orf', 'pef', 'ptx', 'pxn', 'raf', 'raw', 'rwl', 'rw2', 'rwz', 'sr2',
                        'srf', 'srw', 'tif', 'x3f', 'jpg', 'png', 'tif')
    movie_extensions = ('avchd', 'avi', 'mov', 'mp4')

    if file_path.lower().endswith(image_extensions):
        return 'Image'

    if file_path.lower().endswith(movie_extensions):
        return 'Movie'

    else:
        return False


def ingest(ingest_logs, file_list, root_output_dir, config_file):
    no_exif = []
    movies_list = []
    duplicate_files = []
    file_path = []
    processed_files = []
    ignored_volumes = []
    print('\nIngest mode'
          '\nCurrently attached volumes'
          '\nPlease wait as sizes are calculated. ')

    volumes = get_drives()

    for volume in volumes:
        try:
            dir_size = round(shutil.disk_usage(volume).total / 1280000000)
        except PermissionError:
            dir_size = 0
        print(f'- {volume} ({str(dir_size)} gigabytes)')

        if dir_size > 128:
            ignored_volumes.append(volume)

        if volume in ignored_volumes:
            print('  ^ This volume will be ignored')

    print('\nSizes are approximate\n')
    sleep(1)
    event_name = input('What event are these files from?\n> ')
    output_path = root_output_dir + '/' + event_name.strip()

    if os.path.exists(output_path):
        pass

    else:
        os.mkdir(output_path)

    while True:
        for entry in volumes:

            if entry not in ignored_volumes:
                ignored_volumes.append(entry)

                for root, dirs, files in os.walk(entry):
                    if 'C:' not in root:
                        for name in files:
                            if 'OneDrive' not in dirs:
                                file_path.append(os.path.join(root, name))

        print(f'\n{len(file_path)} files to process\n')

        for item in file_path:
            directory = item.split('/')
            file_name = directory[-1]
            file_type = file_is_media(item)
            processed_files.append(item)
            completion = round(len(processed_files) / len(file_path) * 100)

            print('\033[?25l', end='')
            print("\r", end="")
            print(f'{completion} percent processed.', end='\r')

            if has_hidden_attribute(item, file_name) is False:
                if file_type == 'Image':
                    file = open(item, 'rb')
                    tags = exifread.process_file(file, stop_tag='Model')

                    try:
                        tag = str(tags['Image Model'])
                        duplicate(output_path, item, tag, duplicate_files, file_name)
                        camera_dir(output_path, item, tag)
                        file_list.append(output_path + '/' + tag + '/' + os.path.basename(item))

                    except KeyError:
                        tag = 'Other'
                        duplicate(output_path, item, tag, duplicate_files, file_name)
                        missing_exif(item, output_path, no_exif, movies_list, file_type)
                        file_list.append(output_path + '/' + tag + '/' + os.path.basename(item))

                    except PermissionError:
                        pass

                    except shutil.Error:
                        pass

                elif file_type == 'Movie':
                    duplicate(output_path, item, 'Videos', duplicate_files, file_name)
                    missing_exif(item, output_path, no_exif, movies_list, file_type)
                    file_list.append(output_path + '/Videos/' + os.path.basename(item))

        print('\nIngested ' + str(len(file_list)) + ' files\n')
        processed_files.clear()

        if len(no_exif) > 0:
            print('These files did not have camera information in their EXIF data: ')
            for i in no_exif:
                print(i)
            print('They have been placed in a separate folder (Other)\n')

        if len(duplicate_files) > 0:
            print('These files had duplicate filenames: ')
            for i in duplicate_files:
                print(i)
            print('They have been placed in a separate folder (Duplicates)\n')

        if len(movies_list) > 0:
            print('These files were video files: ')
            for i in movies_list:
                print(i)
            print('They have been placed in a separate folder (Videos)\n')

        print('\033[?25h', end='')

        more_files = input('Are there more files to transfer? (Yes/No)'
                           '\nIf you have another storage device, plug it in now.\n')

        if more_files in ['No', 'no', 'N', 'n', 'NO', 'Nup', 'Nah', 'nup', 'nah']:
            new_log = (f'[{str(datetime.today())}] {str(len(file_list))} files ingested by ' +
                       config_file['Program']['Name'])
            ingest_logs.append(new_log)

            no_exif.clear()
            movies_list.clear()
            duplicate_files.clear()
            ignored_volumes.clear()
            processed_files.clear()
            return output_path

        if more_files in ['Yes', 'yes', 'Y', 'y', 'YES']:
            print('Looking for new drives')
            continue

        else:
            print('Type Yes or No')


def delegate(delegate_logs, output, config_file):
    available_files = []
    accounted_files = []
    files_out = output
    types_to_delegate = []
    image_mode = ('1', 'images', 'photos', 'pics')
    video_mode = ('2', 'videos', 'movies', 'vids')
    all_files = ('3', 'all', 'everything', 'all of it mate')
    mode = ""

    if files_out:
        print('Would you like to use the files you just ingested or do you want to select a different folder?'
              '\nPress enter to use ingested files or type New to select a new folder')
        new_folder = input().strip()
        if new_folder == 'New' or new_folder == 'new' or new_folder == 'n' or new_folder == 'New Folder' or \
                new_folder == 'new folder':
            del output

    while not files_out:
        root = tk.Tk()
        root.withdraw()
        files_out = filedialog.askdirectory()

    while not mode:
        selected_mode = input(f'What files would you like to delegate from {str(files_out)}?'
                              f'\n[1] Images'
                              f'\n[2] Videos'
                              f'\n[3] All available files\n').strip().lower()

        if selected_mode in image_mode:
            types_to_delegate.append('Image')
            mode = "Delegated Images"
        elif selected_mode in video_mode:
            types_to_delegate.append('Movie')
            mode = "Delegated Videos"
        elif selected_mode in all_files:
            types_to_delegate.append('Movie')
            types_to_delegate.append("Image")
            mode = "Delegated Files"
        else:
            print("Select a valid option")

    for root, dirs, files in os.walk(files_out):
        for name in files:
            file_path = os.path.join(root, name)
            file_directories = file_path.split("/")
            if "Delegated Files" in file_directories:
                pass
            elif "Delegated Images" in file_directories:
                pass
            elif "Delegated Videos" in file_directories:
                pass
            elif "Duplicates" in file_directories:
                pass
            elif has_hidden_attribute(file_path, name):
                pass
            elif file_is_media(file_path) not in types_to_delegate:
                pass
            else:
                available_files.append(file_path)

    if len(available_files) < 1:
        print("No files to ingest in " + files_out)
    else:
        name_input = input('Write the names of each editor separated by a comma. \n'
                           '(Steve, Matt Smith, Pikachu, Robbie, Anne)\n')
        names = name_input.split(',')

        try:
            os.mkdir(files_out + '/' + mode + '/')

        except FileExistsError:
            pass

        except OSError:
            print('Delegations folder is read only, please check permissions')

        files_len = len(available_files)

        for index, name in enumerate(names):
            name = name.strip()
            each_user = math.ceil(files_len / len(names))
            my_files = []
            files_before = each_user * (index - 1)
            this_editor = []

            for x in range(each_user):
                if available_files[files_before + x] not in accounted_files:
                    my_files.append(available_files[files_before + x])
                    accounted_files.append(available_files[files_before + x])
                else:
                    pass

            path = files_out + "/" + mode + "/" + name + "/"

            if len(my_files) > 0:
                try:
                    os.mkdir(path)

                except FileExistsError:
                    pass

                except FileNotFoundError:
                    print('Folder does not exist')
                    return

                for file in my_files:
                    print(file)
                    shutil.copy(file, path)
                    this_editor.append(file)

                print(f'{name} was delegated {len(this_editor)} files in folder {path}\n')
        new_log = (f'[{str(datetime.today())}] {mode} to {len(names)} people by ' + config_file['Program']['Name'])
        delegate_logs.append(new_log)
        types_to_delegate.clear()


def logs(stored_logs):
    print('Operations completed this session:')
    for i in range(0, len(stored_logs)):
        print(stored_logs[i])
    input('\nPress Enter to go back to the main menu')
    return 0


def main():
    app_dir = "Not Set"
    path = ''
    stored_logs = []
    stored_files = []
    config = configparser.ConfigParser()

    if not os.path.exists('./config.conf'):
        write(config)
        config.add_section('Program')
        stored_logs.append(f'[{str(datetime.today())}] New session created')
    else:
        config.read('./config.conf')

        try:
            config['Program']
        except KeyError:
            config.add_section('Program')

        stored_logs.append(f'[{str(datetime.today())}] New session created')
        try:
            app_dir = config['Program']['Default Output']
            stored_logs = config['Program']['Logs'].split('/')
        except KeyError:
            pass

    try:
        if config['Program']['Name'] is None:
            config.set('Program', 'Name', input("What is your name?\n> ").strip())
    except KeyError:
        config.set('Program', 'Name', input("What is your name?\n> ").strip())
    write(config)

    if os.name == 'posix':
        print("\x1b[8;40;120t")
    if os.name == 'nt':
        os.system("mode 120,40")


    if app_dir == "Not Set":
        input('Press enter to select an output folder')

    while not app_dir or app_dir == "/" or app_dir == "Not Set":
        window = tk.Tk()
        window.withdraw()
        app_dir = filedialog.askdirectory()
        set_default = input("Would you like to save this as your default output directory?\n> ").strip().lower()
        if set_default == "yes" or "y" or "yeah":
            config.set('Program', 'Default Output', app_dir)

    write(config)

    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')

    print(str(config['Program']['Name']) + ' - tooloflife v1.1.0 (' + os.name + ')\nOutput directory: ' + app_dir)
    sleep(0.5)

    while True:
        print('\n[0] About'
              '\n[1] Ingest'
              '\n[2] Delegate'
              '\n[3] Logs'
              '\n[4] Open Folder'
              '\n[5] Quit')
        current_menu = input('> ').strip().lower()

        if current_menu == '0' or current_menu == 'about':
            about()
        elif current_menu == '1' or current_menu == 'ingest':
            path = ingest(stored_logs, stored_files, app_dir, config)
        elif current_menu == '2' or current_menu == 'delegate':
            delegate(stored_logs, path, config)
        elif current_menu == '3' or current_menu == 'logs':
            logs(stored_logs)
        elif current_menu == '4' or current_menu == 'open folder':
            webbrowser.open('file:///' + os.path.realpath(app_dir))
        elif current_menu == '5' or current_menu == 'quit' or current_menu == 'exit':
            break
        else:
            print('Select a valid option')

        logs_to_save = ""
        for log in stored_logs:
            if len(logs_to_save) == 0:
                logs_to_save = log
            else:
                logs_to_save = logs_to_save + '/' + log
        config.set('Program', 'Logs', logs_to_save)
        write(config)


if __name__ == '__main__':
    main()
