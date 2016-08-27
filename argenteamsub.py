#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import json
import zipfile
import os
import re
import argparse

api_url = "http://argenteam.net/api/v1/"
api_search = api_url + "search"
api_episode = api_url + "episode"


def release_to_string(release):
    return "%s %s %s %s" % (release['source'], release['codec'], release['tags'], release['team'])


def match_version(release, version):
    if not version:
        return True
    return release['tags'].lower() in version.lower() \
        and release['team'].lower() in version.lower()


def rename_sub(file, name):
    dir, filename = os.path.split(file)
    _, sub_ext = os.path.splitext(filename)
    destname, _ = os.path.splitext(name)
    os.rename(file, os.path.join(dir, destname + sub_ext))


def extract_sub(zipfilename, dest):
    zip = zipfile.ZipFile(zipfilename)
    for file in zip.namelist():
        if os.path.splitext(file)[1] in ['.srt', '.sub']:
            return zip.extract(file, dest)
    return None


def download_sub(id, version):
    response = urllib.urlopen(api_episode + "?id=" + str(id)).read()
    content = json.loads(response)

    for release in content['releases']:
        release_name = release_to_string(release)
        if match_version(release, version):
            print "Version match: " + release_name
            if release['subtitles']:
                sub = release['subtitles'][0]['uri']
                return urllib.urlretrieve(sub)[0]
            else:
                print "No subtitles found for " + release_name
        else:
            print "Ignoring version: " + release_name

    return None


def search_sub(tvshow, season, episode, version=""):
    search = "%s S%#02dE%#02d" % (tvshow, season, episode)
    print "Searching subtitles for: %s. Version: %s" % (search, version)
    response = urllib.urlopen(api_search + "?q=" + urllib.quote_plus(search)).read()
    content = json.loads(response)
    for result in content['results']:
        if result['type'] == 'episode':
            return result['id']
    return None


def process_sub(tvshow, season, episode, version, dir, filename):
    sub_id = search_sub(tvshow, season, episode, version)
    subzip = download_sub(sub_id, version)
    sub_file = extract_sub(subzip, dir)
    rename_sub(sub_file, filename)


def process_file(dir, filename):
    match = re.match(r'^(?P<tvshow>.*)\WS(?P<season>\d\d)E(?P<episode>\d\d)\W?(?P<version>.*)\.(mkv|avi|mp4)$', filename, flags=re.IGNORECASE)
    if match is not None:
        tvshow = match.group('tvshow').replace('.', ' ')
        season = match.group('season')
        episode = match.group('episode')
        version = match.group('version')
        process_sub(tvshow, int(season), int(episode), version, dir, filename)
    else:
        print "Invalid file: " + file


def process(path):
    if os.path.isfile(path):
        (dir, filename) = os.path.split(os.path.realpath(path))
        process_file(dir, filename)
    else:
        print "Argumento invalido"


parser = argparse.ArgumentParser(description="Argenteam subtitles downloader")
parser.add_argument("file", help="Archivo de video")
args = parser.parse_args()

process(args.file)
