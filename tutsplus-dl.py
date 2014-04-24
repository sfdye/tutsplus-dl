import os
import sys
import time
import math
import requests
from bs4 import BeautifulSoup

def format_bytes(bytes):
    """
    Get human readable version of given bytes.
    Ripped from https://github.com/rg3/youtube-dl
    """
    if bytes is None:
        return 'N/A'
    if type(bytes) is str:
        bytes = float(bytes)
    if bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(bytes, 1024.0))
    suffix = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'][exponent]
    converted = float(bytes) / float(1024 ** exponent)
    return '{0:.2f}{1}'.format(converted, suffix)

class DownloadProgress(object):
    """
    Report download progress.
    Inspired by https://github.com/rg3/youtube-dl
    """

    def __init__(self, total):
        if total in [0, '0', None]:
            self._total = None
        else:
            self._total = int(total)

        self._current = 0
        self._start = 0
        self._now = 0

        self._finished = False

    def start(self):
        self._now = time.time()
        self._start = self._now

    def stop(self):
        self._now = time.time()
        self._finished = True
        self._total = self._current
        self.report_progress()

    def read(self, bytes):
        self._now = time.time()
        self._current += bytes
        self.report_progress()

    def calc_percent(self):
        if self._total is None:
            return '--%'
        percentage = int(float(self._current) / float(self._total) * 100.0)
        done = int(percentage/2)
        return '[{0: <50}] {1}%'.format(done * '#', percentage)

    def calc_speed(self):
        dif = self._now - self._start
        if self._current == 0 or dif < 0.001:  # One millisecond
            return '---b/s'
        return '{0}/s'.format(format_bytes(float(self._current) / dif))

    def report_progress(self):
        """Report download progress."""
        percent = self.calc_percent()
        total = format_bytes(self._total)

        speed = self.calc_speed()
        total_speed_report = '{0} at {1}'.format(total, speed)

        report = '\r{0: <56} {1: >30}'.format(percent, total_speed_report)

        if self._finished:
            print report
        else:
            print report
            print
        sys.stdout.flush()


def download(url):
    """
        download single file from url
    """

    base_dir = os.path.dirname(__file__)

    r = requests.get(url, stream=True)
    course_name = r.url.split('/')[5]
    filename = r.url.split('/')[6][:r.url.split('/')[6].find('?')]
    filesize = (int)(r.headers.get('content-length'))
    
    # create course directory if does not exist
    if not os.path.exists(course_name):
         os.makedirs(course_name)       

    progress = DownloadProgress(filesize)
    chunk_size = 1048576

    if r.ok:
        print '%s found (%.1f M)' % (filename, filesize/1024/1024)
    else:
        print 'Could not find video'
        return 
    
    uri = os.path.join(base_dir, course_name, filename)

    if os.path.isfile(uri):
        if os.path.getsize(uri) != filesize:
            print 'file seems corrupted, download again'
        else:
            print 'already downloaded, skipping...'
            print
            return 

    with open(uri, 'wb') as handle:
        print 'Start downloading...'
        progress.start()
        for chunk in r.iter_content(chunk_size):
            if not chunk:
                progress.stop()
                break
            progress.read(chunk_size)

            handle.write(chunk)
        
        print '%s downloaded' % filename
        print

def main():
    if len(sys.argv) < 2:
        print 'Usage: python tuts_downloader url_to_course'
        return

    url = sys.argv[1]
    r = requests.get(url)
    soup = BeautifulSoup(r.text)

    for section in soup.find_all('tr', 'section-row'):
        lesson_url = section.td.a['href']
        lesson_soup = BeautifulSoup(requests.get(lesson_url).text)
        video_url = lesson_soup.find('div', 'post-buttons').a['href']
        download(video_url)

if __name__ == '__main__':
    main()
