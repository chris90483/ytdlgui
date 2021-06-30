import json
import os.path
from pathlib import Path

from ttkbootstrap import Style

import subprocess
import threading
import youtube_dl

import glob
import os
import time

from tkinter import *
from tkinter.filedialog import askdirectory
import clipboard


class ProgressAnimation(object):
    def __init__(self, canvas, rect):
        self.x = 0
        self.y = 0
        self.is_converting = False
        self.is_downloading = False
        self.canvas = canvas
        self.rect = rect
        self.thread = threading.Thread(target=self.run_converting_animation)
        self.downloaded_percentage = 0
        self.FRAME_INTERVAL = 0.001

    def run_downloading_animation(self):
        last_frame_time = time.time()
        while self.is_downloading:
            if time.time() - last_frame_time > self.FRAME_INTERVAL:
                amount_steps = (time.time() - last_frame_time) // self.FRAME_INTERVAL
                last_frame_time = time.time()
                target_width = (self.canvas.winfo_width() / 100) * self.downloaded_percentage
                if self.y < target_width:
                    self.y += amount_steps
                self.canvas.coords(self.rect, 0, 0, self.y, 30)


    def run_converting_animation(self):
        last_frame_time = time.time()
        while self.is_converting:
            if time.time() - last_frame_time > self.FRAME_INTERVAL:
                amount_steps = (time.time() - last_frame_time) // self.FRAME_INTERVAL
                last_frame_time = time.time()
                self.canvas.coords(self.rect, self.x, 0, self.y, 30)
                canvas_width = self.canvas.winfo_width()
                if self.x == 0:
                    if self.y < 60:
                        self.y += amount_steps
                    else:
                        self.x += amount_steps
                        self.y += amount_steps
                else:
                    if self.y >= canvas_width:
                        if self.x < canvas_width:
                            self.x += amount_steps
                        else:
                            self.x = 0
                            self.y = 0
                    else:
                        self.y += amount_steps
                        self.x += amount_steps

    def to_finished(self):
        last_frame_time = time.time()
        while self.x > 0 or self.y < self.canvas.winfo_width():
            if time.time() - last_frame_time > self.FRAME_INTERVAL:
                amount_steps = (time.time() - last_frame_time) // self.FRAME_INTERVAL
                last_frame_time = time.time()
                if self.x > 0:
                    self.x -= amount_steps
                if self.y < self.canvas.winfo_width():
                    self.y += amount_steps
                self.canvas.coords(self.rect, self.x, 0, self.y, 30)

    def start_downloading(self):
        if not self.is_downloading:
            self.is_downloading = True

            self.canvas.itemconfig(self.rect, fill='#158CBA')
            self.canvas.coords(self.rect, 0, 0, 0, 30)
            self.thread = threading.Thread(target=self.run_downloading_animation)
            self.y = 0
            self.thread.start()


    def start_converting(self):
        self.stop_downloading()
        if not self.is_converting:
            self.is_converting = True

            self.canvas.itemconfig(self.rect, fill='#158CBA')
            self.thread = threading.Thread(target=self.run_converting_animation)
            self.x = 0
            self.y = 60
            self.thread.start()

    def start_finshed(self):
        self.canvas.itemconfig(self.rect, fill='green')
        self.thread = threading.Thread(target=self.to_finished)
        self.thread.start()

    def stop_converting(self):
        if self.is_converting:
            self.is_converting = False
            self.start_finshed()

    def stop_downloading(self):
        if self.is_downloading:
            self.is_downloading = False
            last_frame_time = time.time() * 1000
            while self.y < self.canvas.winfo_width():
                if time.time() * 1000 - last_frame_time > 1:
                    last_frame_time = time.time() * 1000
                    self.y += 1
                self.canvas.coords(self.rect, 0, 0, self.y, 30)
            self.downloaded_percentage = 0

def ydl_progress_hook(d):
    if d['status'] == 'downloading':
        if not app_state.currently_downloading:
            progress_text.insert(END, "Bezig met downloaden..")
            progress_text.see(END)
            app_state.progress_text_position = progress_text.index("end-1c linestart")
            app_state.currently_downloading = True
            progress_animation.start_downloading()
        else:
            progress_text.delete("end-1c linestart", "end")
            downloaded_percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
            progress_animation.downloaded_percentage = downloaded_percentage
            progress_text.insert(app_state.progress_text_position, "Bezig met downloaden (" + "{:.2f}".format(downloaded_percentage) + "%)")
            progress_text.see(app_state.progress_text_position)
    elif d['status'] == 'error':
        app_state.currently_downloading = False
        progress_text.insert(END, "\nMislukt.\n")
        progress_text.see(END)
    elif d['status'] == 'finished':
        app_state.currently_downloading = False
        progress_text.insert(END, "\nDownload klaar. Aan het converteren..\n")
        progress_animation.start_converting()
        progress_text.see(END)


class AppState(object):
    def __init__(self):
        self.downloader_active_folder = str(Path.home())
        self.recorder_state = {
            'active_folder': str(Path.home())
        }
        self.active_file_format = "mp3"
        self.progress_text_position = "1.0"
        self.currently_downloading = False
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [],
            'progress_hooks': [ydl_progress_hook],
        }

    def to_serializable_dict(self):
        self.ydl_opts['progress_hooks'] = [] # can't serialize functions
        return {
            'downloader_active_folder': self.downloader_active_folder,
            'recorder_state': self.recorder_state,
            'active_file_format': self.active_file_format,
            'progress_text_position': self.progress_text_position,
            'currently_downloading': self.currently_downloading,
            'ydl_opts': self.ydl_opts
        }


# function to save the app state
# also called when the application window is closed.
def save_app_state(app_state):
    open('app_state.json', 'w', encoding="utf-8").close()  # deletes the contents
    with open("app_state.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(app_state.to_serializable_dict()))
    exit()


def load_app_state(app_state):
    with open("app_state.json", "r") as f:
        saved_app_state = json.loads(f.read())
        if "downloader_active_folder" in saved_app_state:
            app_state.downloader_active_folder = saved_app_state['downloader_active_folder']
        if "recorder_state" in saved_app_state:
            app_state.recorder_state = saved_app_state['recorder_state']
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


def show_choose_folder_dialog(app_state, current_dir_text, tab):
    if tab == 'downloader':
        app_state.downloader_active_folder = askdirectory()
        current_dir_text.set("Huidige map: " + app_state.downloader_active_folder)
    elif tab == 'recorder':
        app_state.recorder_state['active_folder'] = askdirectory()
        current_dir_text.set("Huidige map: " + app_state.recorder_state['active_folder'])

def download(url_input_entry, app_state):
    progress_text.insert(END, "Begonnen aan een nieuwe download..\n")
    progress_text.see(END)
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
            try:
                ydl.download([url_input_entry_dl.get()])
            except youtube_dl.DownloadError:
                progress_animation.canvas.itemconfig(progress_animation.rect, fill="red")
                progress_animation.is_downloading = False
                progress_text.insert(END, "Download mislukt.\n")
                progress_text.see(END)

        # move the file
        progress_animation.stop_converting()
        list_of_files = glob.glob("*." + app_state.active_file_format)  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        print("moving " + latest_file + " to " + app_state.downloader_active_folder + "/" + latest_file)
        os.replace(latest_file, app_state.downloader_active_folder + "/" + latest_file)
        progress_text.insert(END, "Bestand opgeslagen in " + app_state.downloader_active_folder + ".\n")
        progress_text.see(END)

    threading.Thread(target=dl, args=(url_input_entry, None)).start()


style = Style(theme='lumen')
root = style.master
app = Window(root)

# appstate
app_state = AppState()
if os.path.isfile("app_state.json"):
    app_state = load_app_state(app_state)

# tk setup
root.wm_title("YouTube Downloader")

# tabs
tabs = ttk.Notebook(root)

##################
# DOWNLOADER TAB #
##################

# downloader tab
downloader = Frame(tabs)
downloader.grid_rowconfigure(0, weight=1)
downloader.grid_rowconfigure(1, weight=2)
downloader.grid_columnconfigure(0, weight=1)
tabs.add(downloader, text="Downloader")

# input area (downloader tab)
input_area = Frame(downloader)
input_area.grid_rowconfigure(2, weight=1)
input_area.grid_columnconfigure(1, weight=1)
input_area.grid(row=0, column=0, padx=10, pady=5)

# open dir dialog button
open_dir_button = Button(input_area, text="kies map", command=lambda: show_choose_folder_dialog(app_state, current_dir_text, "downloader"),
                         width=10, height=1)
open_dir_button.grid(row=0, column=0, pady=5)

# current dir text & label
current_dir_text = StringVar(input_area)
current_dir_text.set("Huidige map: " + app_state.downloader_active_folder)
current_dir_label = Label(input_area, textvariable=current_dir_text)
current_dir_label.grid(row=0, column=1, sticky=W)

# file format options
file_format_options = StringVar(input_area)
file_format_options.set(app_state.active_file_format)
file_format_options.trace("w", lambda *args: update_active_file_format(app_state, file_format_options.get(),
                                                                       file_format_text))
file_format_menu = OptionMenu(input_area, file_format_options, "mp3", "flac", "mp4")
file_format_menu.config(width=5)
file_format_menu.grid(row=1, column=0, pady=5, sticky=W)

# file format info text & label
file_format_text = StringVar(input_area)
file_format_text.set(file_format_desc_of(app_state.active_file_format))
file_format_label = Label(input_area, textvariable=file_format_text)
file_format_label.grid(row=1, column=1, sticky=W)

# # URL input field
url_input_label = Label(input_area, text="Link: ")
url_input_label.grid(row=2, column=0, pady=5)

def url_entry_on_right_click(label):
    label.delete(0, END)
    label.insert(0, clipboard.paste())

def url_entry_on_left_click(label):
    label.delete(0, END)

url_input_entry = Entry(input_area, bd=1, width=65)  # bd is border
url_input_entry.bind("<Button-3>", lambda e: url_entry_on_right_click(url_input_entry)) # paste contents on right click
url_input_entry.bind("<Button-1>", lambda e: url_entry_on_left_click(url_input_entry)) # delete contents on left click
url_input_entry.grid(row=2, column=1)

# Download area (downloader tab)
download_area = Frame(downloader)
download_area.grid(row=1, column=0, padx=10, pady=5)

# Download button
download_button = Button(download_area, text="Downloaden", command=lambda: download(url_input_entry, app_state))
download_button.pack(fill=X)

# Progress text
progress_text = Text(download_area, height=5)
progress_text.pack(fill=X)

# Progress bar
progress_bar_canvas = Canvas(download_area, height=30)
progress_bar_canvas.pack(fill=X, pady=5)
progress_bar = progress_bar_canvas.create_rectangle(0, 0, 0, 30, fill='#158CBA')

progress_animation = ProgressAnimation(progress_bar_canvas, progress_bar)

################
# RECORDER TAB #
################

# recorder tab
recorder = Frame(tabs)
tabs.add(recorder, text="Recorder")

# input area (recorder tab)
recorder_input_area = Frame(recorder)
recorder_input_area.pack(fill=X)

# open dir dialog button
recorder_open_dir_button = Button(recorder_input_area, text="kies map", command=lambda: show_choose_folder_dialog(app_state, recorder_current_dir_text, "recorder"),
                         width=10, height=1)
recorder_open_dir_button.grid(row=0, column=0, padx=10, pady=5)

# current dir text & label
recorder_current_dir_text = StringVar(recorder_input_area)
recorder_current_dir_text.set("Huidige map: " + app_state.recorder_state['active_folder'])
recorder_current_dir_label = Label(recorder_input_area, textvariable= recorder_current_dir_text)
recorder_current_dir_label.grid(row=0, column=1, sticky=W)

########
# MAIN #
########

# Expose tabs
tabs.grid_rowconfigure(0, weight=1)
tabs.grid_columnconfigure(0, weight=1)
tabs.pack(expand=1, fill=X)

# Main loop
root.protocol("WM_DELETE_WINDOW", lambda: save_app_state(app_state))
root.mainloop()
