import urllib
import json
import zipfile
import sys
import re

api_url = "http://argenteam.net/api/v1/"
api_search = api_url + "search"
api_episode = api_url + "episode"

def match_version(release, version):
    #TODO
    return True

def download_sub(id, version):
    response = urllib.urlopen(api_episode + "?id=" + str(id)).read()
    content = json.loads(response)

    for release in content['releases']:
        if match_version(release, version):
            sub = release['subtitles'][0]['uri']
            (filename, _) = urllib.urlretrieve(sub)
            zipfile.ZipFile(filename).extractall()
            return sub

def search_sub(tvshow, season, episode, version=""):
    search = "%s s%#02de%#02d" % (tvshow, season, episode)
    response = urllib.urlopen(api_search + "?q=" + search).read()
    content = json.loads(response)

    for result in content['results']:
        download_sub(result['id'], version)

for arg in sys.argv[1:]:
    match = re.match(r'^(?P<tvshow>.*)\WS(?P<season>\d\d)E(?P<episode>\d\d)(?P<version>.*)\.(mkv|avi|mp4)$', arg, flags=re.IGNORECASE)
    if match is not None:
        tvshow = match.group('tvshow')
        season = match.group('season')
        episode = match.group('episode')
        version = match.group('version')
        search_sub(tvshow, int(season), int(episode), version)
    else:
        print "Invalid file: " + arg
