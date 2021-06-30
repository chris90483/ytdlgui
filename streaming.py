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
import path


class RadioRecorder(object):

    def __init__(self, recorder_state):
        self.main_directory = recorder_state['main_directory']
        self.stations = [{
                'url': 'http://freshgrass.streamguys1.com/folkalley-128mp3',
                'name': 'Folk Alley',
                'genre': 'folk',
                'subdirectory': '/folk_alley/'
            }
        ]
        for station in recorder_state['stations']:
            if not station['name'] == 'Folk Alley':
                self.stations.append(station)


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
            sys.exit('no title found')
        return title.decode(encoding, errors='replace')


    def record(self, station):
        r = requests.get(station['url'], stream=True)
        current_title = get_current_title(station['url'])
        with open(path.join(self.main_directory, station['subdirectory'], current_title), 'wb') as f:
            try:
                prev_tick = time.time()
                for block in r.iter_content(1024):
                    f.write(block)
                    if time.time() - prev_tick > 1:
                        prev_tick = time.time()
                        updated_title = get_current_title(url)
                        print(updated_title)
                        if not updated_title == current_title:
                            break
            except KeyboardInterrupt:
                pass
