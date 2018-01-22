#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import argparse
from fuzzywuzzy import fuzz, process
from bs4 import BeautifulSoup
try:
    # For Python 3.0 and later
    from urllib.request import Request, urlopen
except ImportError:
    # Fall back to Python 2's urllib
    from urllib2 import urlopen, Request

URL_BASE = "https://www.tusubtitulo.com/"


def init(path):
    if os.path.isfile(path):
        (dir, filename) = os.path.split(os.path.realpath(path))
        process_file(dir, filename)
    else:
        print("ERROR: El parámetro no es un archivo válido")


def process_file(dir, filename):
    match = re.match(r'^(?P<tvshow>.*)\WS(?P<season>\d\d)E(?P<episode>\d\d)\W?(?P<version>.*)\.(mkv|avi|mp4)$', filename, flags=re.IGNORECASE)
    if match is not None:
        tvshow = match.group('tvshow').title()
        season = int(match.group('season'))
        episode = int(match.group('episode'))
        version = match.group('version').upper()
        show_id = search_show_id(tvshow)
        process_subs(show_id, season, episode, version, dir, filename)
    else:
        print("ERROR. El nombre del archivo debe tener el siguiente formato:")
        print("<serie>S<temporada>E<episodio>[version].(mkv|avi|mp4)")

def search_show_id(show):
    page = urlopen(URL_BASE + 'series.php').read().decode('utf-8')
    regex = show.replace('.', '[\s,.:-]+')
    try:
        link = BeautifulSoup(page, 'html.parser').find('a', text=re.compile(regex)).get('href')
    except:
        exit("Show %s not found" % show)
    return link.split('/')[-1]


def process_subs(show_id, season, episode, version, dir, filename):
    url = "%sajax_loadShow.php?show=%s&season=%s" % (URL_BASE, show_id, season)
    page = urlopen(url).read().decode('utf-8')
    subs = parse_content(page, season, episode)
    (ver, lang, sub_url) = select_sub(subs, version)
    print("Descargando subtitulo para la version %s - %s" % (ver, lang))
    req = Request(sub_url, headers={'Referer': 'https://www.tusubtitulo.com'})
    sub_data = urlopen(req).read()
    print("Subtítulo descargado satisfactoriamente.")
    write_file(sub_data, dir, filename)


def parse_content(page, season, episode):
    html = BeautifulSoup(page, 'html.parser')
    result = {}
    row = html.find('a', text=re.compile("%#1dx%#02d" % (season, episode))).find_parent('tr')
    while True:
        row = row.find_next_sibling()
        if not row: break
        regex = re.search('Versi.n (.*)', row.text)
        if regex:
            v = regex.group(1).strip()
            result[v] = {}
        else:
            if not re.search('Descargar', row.text): break
            lang = row.find('td', class_="language").text.strip()
            result[v][lang] = 'https:' + row.a.get('href')
    return result


def select_sub(subs, version):
    best_version, _ = process.extractOne(version, subs.keys(), scorer=fuzz.token_set_ratio)
    best_lang, _ = process.extractOne(u'Español Latinoamérica', subs[best_version].keys(), scorer=fuzz.token_set_ratio)
    return (best_version, best_lang, subs[best_version][best_lang])


def write_file(sub_data, dir, filename):
    filename, _ = os.path.splitext(filename)
    try:
        f = open(os.path.join(dir, filename + '.srt'), 'b+w')
    except ValueError:
        f = open(os.path.join(dir, filename + '.srt'), 'w')
    f.write(sub_data)

# ------------------------ MAIN ------------------------
parser = argparse.ArgumentParser(description="TuSubtitulo.com Downloader")
parser.add_argument('file', help="Archivo de video")
args = parser.parse_args()

init(args.file)
