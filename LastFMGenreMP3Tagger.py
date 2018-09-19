import pylast
import config
import eyed3
import argparse
import os

API_KEY = config.last_api_key
API_SECRET = config.last_api_secret
username = config.last_u
password_hash = pylast.md5(config.last_p)

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET,
                               username=username, password_hash=password_hash)

parser = argparse.ArgumentParser(description='Update genre tag of mp3s in folder using Last.FM')
parser.add_argument('-p', '--path', nargs=1, required=True, dest='path')
args = parser.parse_args()

folder = args.path[0]

genre_map = {}

for dirName, subdirList, fileList in os.walk(folder):
    print('Found directory: %s' % dirName)
    for fname in fileList:
        if fname.endswith('.mp3'):
            file_path = dirName + '\\' + fname
            audio_file = eyed3.load(file_path)
            artist = audio_file.tag.artist
            # as long as the artist tag is not empty...
            if artist:
                print(audio_file.tag.title)
                print(audio_file.tag.genre)
                if artist in genre_map:
                    audio_file.tag.genre = genre_map[artist]
                    audio_file.tag.save()
                    print('we already have %s' % genre_map[artist])
                    continue
                else:
                    last_artist = network.get_artist(artist)
                    if last_artist:
                        tags = last_artist.get_top_tags(6)
                        top_tag = tags[0]
                        genre_map[artist] = top_tag.item.name
                        print('for the artist %s' % artist)
                        print('we have the last fm artist %s' % last_artist)
                        print('the genres %s' % tags)
                        print('and the top tag %s' % genre_map[artist])
                        audio_file.tag.genre = genre_map[artist]
                        audio_file.tag.save()
