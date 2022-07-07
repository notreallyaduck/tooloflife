import math
import os
import shutil
import stat
import string
import sys
import webbrowser
from datetime import datetime
from time import sleep
import exifread
import tkinter as tk
from tkinter import filedialog
import ctypes
import configparser


class Colour:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def notify(title, text):
    if os.name == 'posix':
        os.system("""
                  osascript -e 'display notification "{}" with title "{}"'
                  """.format(text, title))
    elif os.name == 'nt':
        os.system(f'echo msgbox "{text}" > "%temp%\popup.vbs" wscript.exe "%temp%\popup.vbs"')
    else:
        pass


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
    print(f'\n{Colour.BOLD}{Colour.RED} About this tool\n{Colour.END}'
          '\n This is a tool designed to help streamline the processes regarding file management within the PSHS '
          '\n Multimedia Team.\n'
          '\n Sudesh Arunachalam sends his highest regards on the survival of anyone who uses this piece of software.')
    print('\033[?25l', end='')
    input('\n Press "Enter" to go back to the main menu')
    print('\033[?25h', end='')


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
                print(" Something went wrong: " + file_path)


def camera_dir(output_path, file_path, tag):
    if not os.path.exists(output_path + '/' + tag):
        print(' Camera specific folder for ' + tag + ' does not exist')
        print(' Creating one now')
        os.mkdir(output_path + '/' + tag)
        shutil.copy(file_path, output_path + '/' + tag)

    else:
        shutil.copy(file_path, output_path + '/' + tag)


def file_is_media(file_path, only_raw):
    raw_extensions = ('.3fr', '.ari', '.arw', '.bay', '.braw', '.crw', '.cr2', '.cr3', '.cap', '.dcs', '.dcr', '.x3f',
                      '.dng', 'drf', '.eip', '.erf', '.fff', '.gpr', '.iiq', '.k25', '.kdc', '.mdc', '.mdc', '.mef',
                      '.mos', '.mrw', 'nef', '.nrw', '.obm', '.orf', '.pef', '.ptx', '.pxn', '.raf', '.raw', '.rwl',
                      '.rw2', '.rwz', '.sr2', 'srf', '.srw', '.tif')
    image_extensions = ('.jpg', '.png', '.tif')
    movie_extensions = ('avchd', '.avi', '.mov', '..mp4')

    if not only_raw:
        if file_path.lower().endswith(image_extensions) or file_path.lower().endswith(raw_extensions):
            return 'Image'
    elif only_raw:
        if file_path.lower().endswith(raw_extensions):
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
    ignored_volumes = ['C:\\']
    event_name = 0

    print('\033[?25l', end='')
    print(f'\n{Colour.BOLD}{Colour.RED} Ingest Mode\n{Colour.END}'
          '\n Currently attached volumes'
          '\n Please wait as sizes are calculated. ')

    volumes = get_drives()

    for volume in volumes:
        try:
            dir_size = round(shutil.disk_usage(volume).total / 1280000000)
        except PermissionError:
            dir_size = 0
        print(f' - {volume} ({str(dir_size)} gigabytes)')

        if dir_size > 128:
            ignored_volumes.append(volume)

        if volume in ignored_volumes:
            print('   ^ This volume will be ignored')

    print('\n Sizes are approximate\n')
    sleep(1)
    print('\033[?25h', end='')

    while not event_name:
        event_name = input(f' What event are these files from?'
                           f'\n Type "Cancel" to abort ingest'
                           f'\n {Colour.BOLD}{Colour.GREEN}> ')

    if event_name.lower() == 'cancel' or event_name.lower() == 'abort':
        cancel_ingest = True
    else:
        cancel_ingest = False

    print(Colour.END)
    output_path = root_output_dir + '/' + event_name.strip()

    if not cancel_ingest:
        if os.path.exists(output_path):
            pass

        else:
            os.mkdir(output_path)

        while True:
            for entry in volumes:

                if entry not in ignored_volumes:
                    ignored_volumes.append(entry)

                    for root, dirs, files in os.walk(entry):
                        for name in files:
                            if 'OneDrive' not in dirs:
                                file_path.append(os.path.join(root, name))

            print(f'\n {len(file_path)} files to process\n')

            for item in file_path:
                directory = item.split('/')
                file_name = directory[-1]
                file_type = file_is_media(item, False)
                processed_files.append(item)
                completion = round(len(processed_files) / len(file_path) * 100)

                print('\033[?25l', end='')
                print("\r", end="")
                print(f' {completion} percent processed.', end='\r')

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

            print('\n Ingested ' + str(len(file_list)) + ' files\n')
            processed_files.clear()

            if len(no_exif) > 0:
                print(' These files did not have camera information in their EXIF data: ')
                for i in no_exif:
                    print(' ' + i)
                print(' They have been placed in a separate folder (Other)\n')

            if len(duplicate_files) > 0:
                print(' These files had duplicate filenames: ')
                for i in duplicate_files:
                    print(' ' + i)
                print(' They have been placed in a separate folder (Duplicates)\n')

            if len(movies_list) > 0:
                print(' These files were video files: ')
                for i in movies_list:
                    print(' ' + i)
                print(' They have been placed in a separate folder (Videos)\n')

            print('\033[?25h', end='')

            notify("Ingest Complete", f"Ingested {len(file_list)} files to {output_path}")
            sleep(2)

            more_files = input(' Are there more files to transfer? (Yes/No)'
                               f'\n If you have another storage device, plug it in now.'
                               f'\n {Colour.BOLD}{Colour.GREEN}> ')
            print(Colour.END)

            if more_files in ['No', 'no', 'N', 'n', 'NO', 'Nup', 'Nah', 'nup', 'nah']:
                new_log = (f'[{str(datetime.today())}] {str(len(file_list))} files ingested by ' +
                           config_file['Program']['Name'])
                ingest_logs.append(new_log)

                no_exif.clear()
                movies_list.clear()
                duplicate_files.clear()
                ignored_volumes.clear()
                processed_files.clear()

                print('\033[?25l', end='')
                input(f'{Colour.BOLD}{Colour.RED} Ingest Complete{Colour.END}\n Press "Enter" to return to main menu')
                print('\033[?25h', end='')

                return output_path

            if more_files in ['Yes', 'yes', 'Y', 'y', 'YES']:
                print(' Looking for new drives')
                continue

            else:
                print(' Type Yes or No')
    else:
        print('\033[?25l', end='')
        input(f'{Colour.BOLD}{Colour.RED} Ingest Cancelled{Colour.END}\n Press "Enter" to return to main menu')
        print('\033[?25h', end='')


def delegate(delegate_logs, output, config_file):
    available_files = []
    accounted_files = []
    new_folder = ""
    files_out = output
    cancel_delegate = False
    types_to_delegate = []
    image_mode = ('1', 'images', 'photos', 'pics')
    video_mode = ('2', 'videos', 'movies', 'vids')
    all_files = ('3', 'all', 'everything', 'all of it mate')
    mode = ""

    print(f'{Colour.BOLD}{Colour.RED}\n Delegate Mode\n{Colour.END}')

    if files_out:
        print(' Would you like to use the files you just ingested or do you want to select a different folder?'
              '\n Press "Enter" to use ingested files, type "New" to select a new folder or type "Cancel" to abort')
        new_folder = input(f' {Colour.BOLD}{Colour.GREEN}> ').strip().lower()
        print(Colour.END)

    elif not files_out:
        new_folder = input(' Press "Enter" to select a folder to delegate from or type "Cancel" to abort'
                           f'\n {Colour.BOLD}{Colour.GREEN}> ').strip().lower()
        print(Colour.END)

    if new_folder == 'new' or new_folder == 'n' or new_folder == 'new folder':
        files_out = ""

    elif new_folder == 'cancel' or new_folder == 'abort':
        cancel_delegate = True

    elif not new_folder:
        pass

    else:
        print(' Select a valid option\n')
        cancel_delegate = True

    if not cancel_delegate:
        while not files_out:
            root = tk.Tk()
            root.withdraw()
            files_out = filedialog.askdirectory()

        while not mode:
            selected_mode = input(f' What files would you like to delegate from {str(files_out)}?'
                                  f'\n [1] Images (Excluding non-RAW images)'
                                  f'\n [2] Videos'
                                  f'\n [3] All available files\n {Colour.BOLD}{Colour.GREEN}> ').strip().lower()
            print(Colour.END)

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
                print(" Select a valid option")

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
                elif file_is_media(file_path, True) not in types_to_delegate:
                    pass
                else:
                    available_files.append(file_path)

        if len(available_files) < 1:
            print(" No files to ingest in " + files_out)
        else:
            name_input = input(' Write the names of each editor separated by a comma. \n'
                               f' (Steve, Matt Smith, Pikachu, Robbie, Anne)\n {Colour.BOLD}{Colour.GREEN}> ')
            print(Colour.END)
            names = name_input.split(',')

            try:
                os.mkdir(files_out + '/' + mode + '/')

            except FileExistsError:
                pass

            except OSError:
                print(' Delegations folder is read only, please check permissions')

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
                        print(' Folder does not exist')
                        return

                    for file in my_files:
                        print(' ' + file)
                        shutil.copy(file, path)
                        this_editor.append(file)

                    print(f' {name} was delegated {len(this_editor)} files in folder {path}\n')

            notify("Delegation Complete", f"{mode} to {len(names)} people")
            sleep(2)

            new_log = (f'[{str(datetime.today())}] {mode} to {len(names)} people by ' + config_file['Program']['Name'])
            delegate_logs.append(new_log)
            types_to_delegate.clear()

            print('\033[?25l', end='')
            input(f'{Colour.BOLD}{Colour.GREEN} Delegate Complete{Colour.END}\n Press "Enter" to return to main menu')
            print('\033[?25h', end='')
    else:
        print('\033[?25l', end='')
        input(f'{Colour.BOLD}{Colour.RED} Delegate Cancelled{Colour.END}\n Press "Enter" to return to main menu')
        print('\033[?25h', end='')


def logs(stored_logs):
    print(f'{Colour.BOLD}{Colour.RED}\n Operations Completed\n{Colour.END}')
    for i in range(0, len(stored_logs)):
        print(" " + stored_logs[i])

    print('\033[?25l', end='')
    input('\n Press "Enter" to go back to the main menu')
    print('\033[?25h', end='')

    return 0


def main():
    app_dir = "Not Set"
    path = ''
    stored_logs = []
    stored_files = []
    config = configparser.ConfigParser()

    if sys.executable.endswith('tooloflife'):
        cur_dir = sys.executable[:-10]
        os.chdir(cur_dir)
    elif sys.executable.endswith('tooloflife.exe'):
        cur_dir = sys.executable[:-14]
        os.chdir(cur_dir)

    if not os.path.exists(f'{os.getcwd()}/config.conf'):
        write(config)
        config.add_section('Program')
    else:
        config.read(f'{os.getcwd()}/config.conf')

        try:
            config['Program']
        except KeyError:
            config.add_section('Program')

        try:
            if os.name == 'nt':
                app_dir = ""
                output_directory = config['Program']['Default Output'].split('/')
                for output in output_directory:
                    if not app_dir:
                        app_dir = output
                    else:
                        app_dir = app_dir + '\\' + output
            else:
                app_dir = config['Program']['Default Output']

            stored_logs = config['Program']['Logs'].split('/')
        except KeyError:
            pass

    stored_logs.append(f'[{str(datetime.today())}] New session created')

    if os.name == 'posix':
        os.system('clear')
        print("\x1b[8;40;150t")
    elif os.name == 'nt':
        os.system('cls')
        os.system("mode 150,40")

    try:
        if config['Program']['Name'] is None:
            config.set('Program', 'Name', input(f" What is your name?\n{Colour.BOLD}{Colour.GREEN} > ").strip())
            print(Colour.END)
    except KeyError:
        config.set('Program', 'Name', input(f" What is your name?\n{Colour.BOLD}{Colour.GREEN} > ").strip())
        print(Colour.END)
    write(config)

    if app_dir == "Not Set":
        print('\033[?25l', end='')
        input(' Press "Enter" to select an output folder')
        print('\033[?25h', end='')

    while not app_dir or app_dir == "/" or app_dir == "Not Set":
        window = tk.Tk()
        window.withdraw()
        app_dir = filedialog.askdirectory()
        set_default = input(" Would you like to save this as your default output directory?"
                            f"\n {Colour.BOLD}{Colour.GREEN}> ").strip().lower()
        print(Colour.END)
        if set_default == "yes" or "y" or "yeah":
            config.set('Program', 'Default Output', app_dir)

    write(config)

    if os.name == 'posix':
        os.system('clear')
        print("\x1b[8;39;150t")
    elif os.name == 'nt':
        os.system('cls')
        os.system("mode 150,39")

    sleep(0.5)

    while True:
        if os.name == 'posix':
            os.system('clear')
        elif os.name == 'nt':
            os.system('cls')

        print('\033[?25l', end='')

        print(f'{Colour.BOLD}{Colour.RED}\n Main Menu\n{Colour.END}')
        sleep(0.1)
        print(' ' + str(config['Program']['Name']) + ' - tooloflife v1.2.0 (' + os.name + ')')
        sleep(0.1)
        print(' Output directory: ' + app_dir)
        sleep(0.1)
        print(" Program directory: " + os.getcwd())
        sleep(0.7)

        print('\033[?25h', end='')

        print('\n [0] About'
              '\n [1] Ingest'
              '\n [2] Delegate'
              '\n [3] Logs'
              '\n [4] Open Folder'
              '\n [5] Quit')
        current_menu = input(f' {Colour.BOLD}{Colour.GREEN}> ').strip().lower()
        print(Colour.END)

        if os.name == 'posix':
            os.system('clear')
        elif os.name == 'nt':
            os.system('cls')

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
            print(' Select a valid option')

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
