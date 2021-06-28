import json
import os.path
from pathlib import Path

from ttkbootstrap import Style

import subprocess
import _thread
import youtube_dl

import glob
import os

from tkinter import *
from tkinter.filedialog import askdirectory


def ydl_progress_hook(d):
    if d['status'] == 'downloading':
        if not app_state.currently_downloading:
            progress_text.insert(END, "Bezig met downloaden..")
            progress_text.see(END)
            app_state.progress_text_position = progress_text.index("end-1c linestart")
            app_state.currently_downloading = True
        else:
            progress_text.delete("end-1c linestart", "end")
            #progress_text.tag_add(app_state.progress_text_position, "1.0", "1.1000")
            #progress_text.tag_config(app_state.progress_text_position, background="black", foreground="white")
            # todo: achtergrond kleurtjes werken nog niet
            progress_text.insert(app_state.progress_text_position, "Bezig met downloaden (" + "{:.2f}".format((d['downloaded_bytes'] / d['total_bytes']) * 100) + "%)")
            progress_text.see(app_state.progress_text_position)
    elif d['status'] == 'error':
        app_state.currently_downloading = False
        progress_text.insert(END, "\nMislukt.\n")
        progress_text.see(END)
    elif d['status'] == 'finished':
        app_state.currently_downloading = False
        progress_text.insert(END, "\nDownload klaar. Aan het converteren..\n")
        progress_text.see(END)

class AppState:
    active_folder = str(Path.home())
    active_file_format = "mp3"
    progress_text_position = "1.0"
    currently_downloading = False
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [],
        'progress_hooks': [ydl_progress_hook],
    }

    def __init__(self):
        pass


# function to save the app state
# also called when the application window is closed.
def save_app_state(app_state):
    app_state.ydl_opts['progress_hooks'] = [] # functions cannot be saved.
    open('app_state.json', 'w', encoding="utf-8").close()  # deletes the contents
    with open("app_state.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(app_state.__dict__))
    exit()


def load_app_state(app_state):
    with open("app_state.json", "r") as f:
        saved_app_state = json.loads(f.read())
        if "active_folder" in saved_app_state:
            app_state.active_folder = saved_app_state['active_folder']
        if "active_file_format" in saved_app_state:
            app_state.active_file_format = saved_app_state['active_file_format']
        if "ydl_opts" in saved_app_state:
            app_state.ydl_opts = saved_app_state['ydl_opts']
        return app_state


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master


def file_format_desc_of(file_format):
    if file_format == "mp3":
        return "MP3: Alleen audio met compressie (lagere kwaliteit, compacter)"
    if file_format == "flac":
        return "FLAC: Alleen audio zonder compressie (Hogere kwaliteit, kost meer geheugen)"
    if file_format == "mp4":
        return "MP4: Audio en video met compressie (lagere kwaliteit, compacter)"


def update_active_file_format(app_state, chosen, file_format_text):
    app_state.active_file_format = chosen
    file_format_text.set(file_format_desc_of(chosen))


def show_choose_folder_dialog(app_state, current_dir_text):
    app_state.active_folder = askdirectory()
    current_dir_text.set("Huidige map: " + app_state.active_folder)

def download(url_input_entry, app_state):
    if app_state.active_file_format == "mp3":
        app_state.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [ydl_progress_hook]
        }
    elif app_state.active_file_format == "mp4":
        app_state.ydl_opts = {
            'format': 'mp4',
            'postprocessors': [],
            'progress_hooks': [ydl_progress_hook]
        }
    elif app_state.active_file_format == "flac":
        app_state.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'flac',
            }],
            'progress_hooks': [ydl_progress_hook]
        }
    def dl(url_input_entry_dl, _foo):
        with youtube_dl.YoutubeDL(app_state.ydl_opts) as ydl:
            ydl.download([url_input_entry_dl.get()])

        # move the file
        list_of_files = glob.glob("*." + app_state.active_file_format)  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        print("moving " + latest_file + " to " + app_state.active_folder + "/" + latest_file)
        os.replace(latest_file, app_state.active_folder + "/" + latest_file)
        progress_text.insert(END, "Bestand opgeslagen in " + app_state.active_folder + ".\n")
        progress_text.see(END)

    _thread.start_new_thread(dl, (url_input_entry, None))

style = Style(theme='lumen')
root = style.master
app = Window(root)

# appstate
app_state = AppState()
if os.path.isfile("app_state.json"):
    app_state = load_app_state(app_state)

# tk setup
root.wm_title("YouTube Downloader")
root.geometry("800x600")

# current dir text & label
current_dir_text = StringVar(root)
current_dir_text.set("Huidige map: " + app_state.active_folder)
current_dir_label = Label(root, textvariable=current_dir_text)
current_dir_label.pack()
current_dir_label.place(x=95, y=13)

# open dir dialog button
open_dir_button = Button(root, text="kies map", command=lambda: show_choose_folder_dialog(app_state, current_dir_text),
                         width=10, height=1)
open_dir_button.pack()
open_dir_button.place(x=10, y=10)

# file format info text & label
file_format_text = StringVar(root)
file_format_text.set(file_format_desc_of(app_state.active_file_format))
file_format_label = Label(root, textvariable=file_format_text)
file_format_label.pack()
file_format_label.place(x=95, y=40)

# file format options
file_format_options = StringVar(root)
file_format_options.set("mp3")
file_format_options.trace("w", lambda *args: update_active_file_format(app_state, file_format_options.get(),
                                                                       file_format_text))
file_format_menu = OptionMenu(root, file_format_options, "mp3", "flac", "mp4")
file_format_menu.pack()
file_format_menu.place(x=10, y=40)

# URL input field
url_input_label = Label(root, text="Link (plakken met ctrl V):")
url_input_label.pack()
url_input_label.place(x=150, y=100)
url_input_entry = Entry(root, bd=1, width=50)  # bd is border
url_input_entry.pack()
url_input_entry.place(x=290, y=100)

# Progress text
progress_text = Text(root, width=90, height=25)
progress_text.pack()
progress_text.place(x=25, y=180)

# Download button
download_button = Button(root, text="Downloaden", command=lambda: download(url_input_entry, app_state))
download_button.pack()
download_button.place(x=330, y=140)

root.protocol("WM_DELETE_WINDOW", lambda: save_app_state(app_state))
root.mainloop()
