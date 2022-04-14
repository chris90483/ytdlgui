#!/usr/bin/env python
from __future__ import print_function
import re
import struct
import sys
try:
    import urllib2
except ImportError:  # Python 3
    import urllib.request as urllib2
import requests
import time
import os
import threading
import vlc


class VlcManager:
    def __init__(self):
        self.vlc_instance = vlc.Instance()
        self.active_player = None
        self.is_playing = False

    def play(self):
        if self.active_player is not None:
            self.active_player.play()
            self.is_playing = True
        else:
            print("tried to play() but active_player is None (call setup_player first).")

    def stop(self):
        if self.active_player is not None:
            self.active_player.stop()
        self.is_playing = False

    def setup_player(self, url):
        self.stop()
        self.active_player = self.vlc_instance.media_player_new()
        self.active_player.set_media(self.vlc_instance.media_new(url))


class RadioRecorder(object):

    def __init__(self, app_state):
        self.active_folder = app_state.recorder_state['active_folder']
        self.stations = [{
                'url': 'http://freshgrass.streamguys1.com/folkalley-128mp3',
                'name': 'Folk Alley',
                'genre': 'folk',
                'subdirectory': 'folk_alley'
            }
        ]
        for station in app_state.recorder_state['stations']:
            if not station['name'] == 'Folk Alley':
                self.stations.append(station)
        self.create_directories()
        self.vlc_manager = VlcManager()
        self.is_recording = False
        self.recorder_thread = None

    def close(self):
        self.stop_recording()

    def create_directories(self):
        for station in self.stations:
            if not os.path.exists(os.path.join(os.path.abspath(self.active_folder), station['subdirectory'])):
                os.mkdir(os.path.join(os.path.abspath(self.active_folder), station['subdirectory']))
                print(f"folder {os.path.join(os.path.abspath(self.active_folder), station['subdirectory'])} created.")

    def lookup_station(self, station_name):
        for station in self.stations:
            if station['name'] == station_name:
                return station
        return None

    def get_current_title(self, url):
        encoding = 'latin1' # default: iso-8859-1 for mp3 and utf-8 for ogg streams
        request = urllib2.Request(url, headers={'Icy-MetaData': 1})  # request metadata
        response = urllib2.urlopen(request)
        metaint = int(response.headers['icy-metaint'])
        for _ in range(10): # # title may be empty initially, try several times
            response.read(metaint)  # skip to metadata
            metadata_length = struct.unpack('B', response.read(1))[0] * 16  # length byte
            metadata = response.read(metadata_length).rstrip(b'\0')
            # extract title from the metadata
            m = re.search(br"StreamTitle='([^']*)';", metadata)
            if m:
                title = m.group(1)
                if title:
                    break
        else:
            print('no title found')
            return "untitled"
        return title.decode(encoding, errors='replace')

    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.vlc_manager.stop()

    def record(self, station_name, ui_elements):
        if self.is_recording:
            self.stop_recording()
        active_station = self.lookup_station(station_name)

        if active_station is None:
            print(f"in functie streaming.record(): {station_name} niet gevonden.")
            return

        # vlc playback regardless of recording state
        self.vlc_manager.setup_player(active_station['url'])
        self.vlc_manager.play()

        r = requests.get(active_station['url'], stream=True)
        current_title = self.get_current_title(active_station['url'])
        ui_elements['now_recording'].set(f"Nu aan het opnemen: {current_title}")

        if os.path.exists(os.path.join(os.path.abspath(self.active_folder), active_station['subdirectory'], current_title + ".mp3")):
            ui_elements['now_recording'].set(f"Bestand {current_title} bestaat al, niet aan het opnemen")
            print(f"path {os.path.join(os.path.abspath(self.active_folder), active_station['subdirectory'], current_title)}.mp3 exists already, skipping")
            return

        ############################################
        # From here the state is_recording is True #
        ############################################
        self.is_recording = True
        def do_record(recorder_self, active_station_arg, current_title_arg, ui_elements_arg):
            with open(os.path.join(os.path.abspath(recorder_self.active_folder), active_station_arg['subdirectory'], current_title + ".mp3"), 'wb+') as f:
                try:
                    prev_tick = time.time()
                    for block in r.iter_content(1024):
                        f.write(block)
                        if time.time() - prev_tick > 1:
                            prev_tick = time.time()
                            updated_title = recorder_self.get_current_title(active_station_arg['url'])
                            if not updated_title == current_title_arg:
                                ui_elements_arg['now_recording'].set(f"Klaar met het opnemen van {current_title_arg}")
                                break
                            if not self.is_recording:
                                ui_elements_arg['now_recording'].set(f"Opnemen gestopt.")
                                break
                except KeyboardInterrupt:
                    pass

        self.recorder_thread = threading.Thread(target=do_record, args=(self, active_station, current_title, ui_elements))
        self.recorder_thread.start()
