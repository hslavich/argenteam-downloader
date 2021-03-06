#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------- IMPORTS -----------------------
import json
import zipfile
import os
import re
import argparse
try:
    # For Python 3.0 and later
    from urllib.request import urlopen, urlretrieve
    from urllib.parse import quote_plus
except ImportError:
    # Fall back to Python 2's urllib
    from urllib2 import urlopen
    from urllib import quote_plus, urlretrieve

# ----------------------- CONSTS -----------------------
API_URL = "http://argenteam.net/api/v1/"
API_SEARCH = API_URL + "search"
API_EPISODE = API_URL + "episode"

# --------------------- FUNCTIONS ----------------------
def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def version_str(release):
    version = ""
    for tag in release['tags'].split():
        version += "%s." % (tag)
    version += "%s.%s-%s" % (release['source'], release['codec'], release['team'])
    return version


def match_version(release, version):
    version_lower = version.lower()
    match = release['source'].lower() in version_lower \
        and release['team'].lower() in version_lower \
        and release['codec'].lower() in version_lower
    if match:
        for tag in release['tags'].split():
            match = match and tag.lower() in version_lower
    return match


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


def download_sub(release):
    print(u"Descargando subtítulo para la versión '%s' .." % version_str(release))
    sub = release['subtitles'][0]['uri']
    return urlretrieve(sub)[0]


def releases_menu(version, alt_version):
    while True:
        if version:
            print("No hay subtítulo para la versión '%s'" % (version))
        print("\nEstas son las opciones disponibles:")
        i = 1
        for release in alt_version:
            print(u"%s. Descargar versión '%s'" % (str(i), version_str(release)))
            i += 1
        print("%s. Salir" % (str(i)))
        selection = input("Seleccione una opción: ")
        if isInt(selection):
            int_selection = int(selection)
            if int_selection >= 1 and int_selection < i:
                print("")
                return alt_version[int_selection-1]
            elif int_selection == i:
                return None
        input("\nOpción inválida. Presione ENTER para volver a intentarlo.")
        os.system('clear')


def search_sub(id, version):
    print("Episodio encontrado, buscando subtítulos ..")
    alt_version = list()
    response = urlopen(API_EPISODE + "?id=" + str(id))
    str_response = response.read().decode('utf-8')
    content = json.loads(str_response)
    for release in content['releases']:
        if release['subtitles']:
            if match_version(release, version):
                return release
            else:
                alt_version.append(release)
    # Couldn't find the right subtitle..
    if alt_version and args.alt: # ..offer the alternative ones
        return releases_menu(version, alt_version)
    print("Lo siento, todavía no hay ningún subtítulo.")
    return None


def search_episode(tvshow, season, episode):
    search = "%s S%#02dE%#02d" % (tvshow, season, episode)
    os.system('clear')
    print("Buscando episodio '%s' .." % (search))
    response = urlopen(API_SEARCH + "?q=" + quote_plus(search))
    str_response = response.read().decode('utf-8')
    content = json.loads(str_response)
    for result in content['results']:
        if result['type'] == 'episode':
            return result['id']
    print("El episodio no se encuentra disponible.")
    return None


def process_sub(tvshow, season, episode, version, dir, filename):
    episode_id = search_episode(tvshow, season, episode)
    if episode_id is not None:
        release = search_sub(episode_id, version)
        if release is not None:
            sub_zip = download_sub(release)
            sub_file = extract_sub(sub_zip, dir)
            rename_sub(sub_file, filename)
            print("Subtítulo descargado satisfactoriamente.")


def process_file(dir, filename):
    match = re.match(r'^(?P<tvshow>.*)\WS(?P<season>\d\d)E(?P<episode>\d\d)\W?(?P<version>.*)\.(mkv|avi|mp4)$', filename, flags=re.IGNORECASE)
    if match is not None:
        tvshow = match.group('tvshow').replace('.', ' ').title()
        season = int(match.group('season'))
        episode = int(match.group('episode'))
        version = match.group('version').upper()
        process_sub(tvshow, season, episode, version, dir, filename)
    else:
        print("ERROR. El nombre del archivo debe tener el siguiente formato:")
        print("<serie>S<temporada>E<episodio>[version].(mkv|avi|mp4)")


def process(path):
    if os.path.isfile(path):
        (dir, filename) = os.path.split(os.path.realpath(path))
        process_file(dir, filename)
    else:
        print("ERROR: El parámetro no es un archivo válido")


# ------------------------ MAIN ------------------------
parser = argparse.ArgumentParser(description="aRGENTeaM Subtitles Downloader")
parser.add_argument('file', help="Archivo de video")
parser.add_argument('--no-alt', dest='alt', action='store_false', help="No ofrecer subtítulos alternativos")
args = parser.parse_args()

process(args.file)
