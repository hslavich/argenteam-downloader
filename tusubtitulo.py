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
        tvshow = match.group('tvshow').replace('.', '-').title()
        season = int(match.group('season'))
        episode = int(match.group('episode'))
        version = match.group('version').upper()
        process_subs(tvshow, season, episode, version, dir, filename)
    else:
        print("ERROR. El nombre del archivo debe tener el siguiente formato:")
        print("<serie>S<temporada>E<episodio>[version].(mkv|avi|mp4)")


def process_subs(tvshow, season, episode, version, dir, filename):
    url = "%sserie/%s/%#02d/%#02d/0" % (URL_BASE, tvshow, season, episode)
    page = urlopen(url).read().decode('utf-8')
    subs = parse_content(page)
    (ver, lang, sub_url) = select_sub(subs, version)
    print("Descargando subtitulo para la version %s - %s" % (ver, lang))
    req = Request(sub_url, headers={'Referer': 'https://www.tusubtitulo.com'})
    sub_data = urlopen(req).read()
    print("Subtítulo descargado satisfactoriamente.")
    write_file(sub_data, dir, filename)


def parse_content(page):
    soup = BeautifulSoup(page, 'html.parser')
    result = {}
    for v in soup.find_all(id=re.compile("version")):
        version = re.search(r'Versi.n (.*?),', v.find(class_="title-sub").text).group(1)
        if not version in result: result[version] = {}
        for sub in v.find_all(class_="sslist"):
            idioma = sub.find(class_="li-idioma").text.strip()
            for link in sub.find_all("a"):
                if 'Descargar' == link.text or u'más actualizado' in link.text:
                    url = re.search(r'href=\"(.*?)\"', str(link)).group(1)
                    result[version][idioma] = URL_BASE + url
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
