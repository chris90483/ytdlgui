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
import clipboard


def ydl_progress_hook(d):
    if d['status'] == 'downloading':
        if not app_state.currently_downloading:
            progress_text.insert(END, "Bezig met downloaden..")
            progress_text.see(END)
            app_state.progress_text_position = progress_text.index("end-1c linestart")
            app_state.currently_downloading = True
        else:
            progress_text.delete("end-1c linestart", "end")
            downloaded_percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
            progress_text.insert(app_state.progress_text_position, "Bezig met downloaden (" + "{:.2f}".format(downloaded_percentage) + "%)")
            progress_bar_canvas.coords(progress_bar, 0, 0, (progress_bar_canvas.winfo_width() / 100) * downloaded_percentage, 30)
            progress_text.see(app_state.progress_text_position)
    elif d['status'] == 'error':
        app_state.currently_downloading = False
        progress_bar_canvas.coords(progress_bar, 0, 0, 0, 30)
        progress_text.insert(END, "\nMislukt.\n")
        progress_text.see(END)
    elif d['status'] == 'finished':
        app_state.currently_downloading = False
        progress_bar_canvas.coords(progress_bar, 0, 0, 0, 30)
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

# input area
input_area = Frame(root)
input_area.pack(fill=X)

# open dir dialog button
open_dir_button = Button(input_area, text="kies map", command=lambda: show_choose_folder_dialog(app_state, current_dir_text),
                         width=10, height=1)
open_dir_button.grid(row=0, column=0, padx=10, pady=5)

# current dir text & label
current_dir_text = StringVar(input_area)
current_dir_text.set("Huidige map: " + app_state.active_folder)
current_dir_label = Label(input_area, textvariable=current_dir_text)
current_dir_label.grid(row=0, column=1, sticky=W)

# file format options
file_format_options = StringVar(input_area)
file_format_options.set(app_state.active_file_format)
file_format_options.trace("w", lambda *args: update_active_file_format(app_state, file_format_options.get(),
                                                                       file_format_text))
file_format_menu = OptionMenu(input_area, file_format_options, "mp3", "flac", "mp4")
file_format_menu.config(width=7)
file_format_menu.grid(row=1, column=0, pady=5)

# file format info text & label
file_format_text = StringVar(input_area)
file_format_text.set(file_format_desc_of(app_state.active_file_format))
file_format_label = Label(input_area, textvariable=file_format_text)
file_format_label.grid(row=1, column=1, sticky=W)

# # URL input field
url_input_label = Label(input_area, text="Link: ")
url_input_label.grid(row=2, column=0, padx=10, pady=5)

def url_entry_on_right_click(label):
    label.delete(0, END)
    label.insert(0, clipboard.paste())

def url_entry_on_left_click(label):
    label.delete(0, END)

url_input_entry = Entry(input_area, bd=1, width=50)  # bd is border
url_input_entry.bind("<Button-3>", lambda e: url_entry_on_right_click(url_input_entry)) # paste contents on right click
url_input_entry.bind("<Button-1>", lambda e: url_entry_on_left_click(url_input_entry)) # delete contents on left click
url_input_entry.grid(row=2, column=1)

# Download area
download_area = Frame(root)
download_area.pack(fill=X, padx=10)

# Download button
download_button = Button(download_area, text="Downloaden", command=lambda: download(url_input_entry, app_state))
download_button.pack(fill=X, padx=10)

# Progress text
progress_text = Text(download_area, width=60, height=8)
progress_text.pack(fill=X, padx=10)

# Progress bar
progress_bar_canvas = Canvas(download_area, height=30)
progress_bar_canvas.pack(fill=X, padx=10, pady=5)
progress_bar = progress_bar_canvas.create_rectangle(0, 0, 0, 30, fill='#158CBA')

root.protocol("WM_DELETE_WINDOW", lambda: save_app_state(app_state))
root.mainloop()

