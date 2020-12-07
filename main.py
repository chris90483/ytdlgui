import json
import os.path
from pathlib import Path

import subprocess
import threading

from tkinter import *
from tkinter.filedialog import askdirectory

class AppState:
    active_folder = str(Path.home())
    active_file_format = "mp3"
    
    def __init__(self):
        pass

# function to save the app state
# also called when the application window is closed.
def save_app_state(app_state):
    open('app_state.json', 'w', encoding="utf-8").close() # deletes the contents
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

def download(url_input_entry, progress_text):
    def dl(url_input_entry, progress_text):
        video_title = "<onbekend>"
        print("Het mitochondrium")
        ytdl_process = subprocess.Popen(["youtube-dl.exe", "--extract-audio", "--audio-format", "mp3", url_input_entry.get()], stdout=subprocess.PIPE)
        print("is de energieleverancier van de cel.")
        
        for line in ytdl_process.stdout:
            str_line = str(line)
            if str_line.find("Destination:") > -1:
                video_title = str_line[24:]
            if str_line.find("youtube") > -1:
                progress_text.insert(END, "YouTube-gegevens ophalen..\n")
            if str_line.find("download") > -1:
                progress_text.insert(END, "Bezig met downloaden..\n")
            if str_line.find("ffmpeg") > -1:
                progress_text.insert(END, "Bezig met converteren..\n")
            progress_text.see(END)
        (output, err) = ytdl_process.communicate()
        exit_code = ytdl_process.wait()
        progress_text.insert(END, "Klaar, bestand opgeslagen als:\n" + video_title + "\n\n")
        progress_text.see(END)
    
    progress_text.insert(END, "Bezig met een niewe video..\n")
    progress_text.see(END)
    ydl_thread = threading.Thread(target=dl, args=(url_input_entry, progress_text))
    
    ydl_thread.start()
    ydl_thread.join()
    

root = Tk()
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
current_dir_label.place(x = 95, y = 13)

# open dir dialog button
open_dir_button = Button(root, text="kies map", command = lambda: show_choose_folder_dialog(app_state, current_dir_text), width = 10, height = 1)
open_dir_button.pack()
open_dir_button.place(x = 10, y = 10)

# file format info text & label
file_format_text = StringVar(root)
file_format_text.set(file_format_desc_of(app_state.active_file_format))
file_format_label = Label(root, textvariable=file_format_text)
file_format_label.pack()
file_format_label.place(x = 95, y = 40)

# file format options
file_format_options = StringVar(root)
file_format_options.set("mp3")
file_format_options.trace("w", lambda *args: update_active_file_format(app_state, file_format_options.get(), file_format_text))
file_format_menu = OptionMenu(root, file_format_options, "mp3", "flac", "mp4")
file_format_menu.pack()
file_format_menu.place(x = 10, y = 40)

# URL input field
url_input_label = Label(root, text="Link:")
url_input_label.pack()
url_input_label.place(x = 200, y = 100)
url_input_entry = Entry(root, bd=1, width=50) # bd is border
url_input_entry.pack()
url_input_entry.place(x = 235, y = 100)

# Progress text
progress_text = Text(root, width = 90, height = 25)
progress_text.pack()
progress_text.place(x = 25, y = 180)

# Download button
download_button = Button(root, text="Downloaden", command = lambda: download(url_input_entry, progress_text))
download_button.pack()
download_button.place(x = 330, y = 140)

root.protocol("WM_DELETE_WINDOW", lambda: save_app_state(app_state))
root.mainloop()
