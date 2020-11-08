import re
import os
import time

from tqdm import tqdm
from datetime import datetime
from google.cloud import texttospeech
from tempfile import TemporaryDirectory
from google.api_core.exceptions import InternalServerError
from pathlib import Path
from mutagen.flac import FLAC
from mutagen.flac import Picture
from mutagen import id3
from PIL import Image

MAX_REQUESTS_PER_MINUTE = 200
MAX_CHARS_PER_MINUTE = 135000


class Narrator:

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, author):
        self._author = author

    @property
    def album_title(self):
        return self._album_title

    @album_title.setter
    def album_title(self, album_title):
        self._album_title = album_title

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def track_number(self):
        return self._track_number

    @track_number.setter
    def track_number(self, track_number):
        self._track_number = track_number

    @property
    def coverfile(self):
        return self._coverfile

    @coverfile.setter
    def coverfile(self, coverfile):
        self._coverfile = coverfile

    def __init__(self, voice_name="en-US-Wavenet-D"):
        self.client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name=voice_name
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )
        # rate limit stuff
        self._minute = -1
        self._requests_this_minute = 0
        self._chars_this_minute = 0
        self._chunk_counter = 1
        self._coverfile = ''

    def print_voice_names(self, lang="en"):
        print("Available voices for language {}:".format(lang))
        for voice in self.client.list_voices().voices:
            if voice.name.startswith(lang):
                print(voice.name)

    def _rate_limit(self):
        if (
            self._requests_this_minute > MAX_REQUESTS_PER_MINUTE
            or self._chars_this_minute > MAX_CHARS_PER_MINUTE
        ):
            while datetime.now().minute == self._minute:
                time.sleep(5)
        if datetime.now().minute != self._minute:
            self._minute = datetime.now().minute
            self._requests_this_minute = 0
            self._chars_this_minute = 0

    def _text_chunk_to_audio_chunk(self, text_chunk):
        self._rate_limit()
        input_text = texttospeech.SynthesisInput(text=text_chunk)
        response = self.client.synthesize_speech(
            input=input_text, voice=self.voice, audio_config=self.audio_config
        )
        self._requests_this_minute += 1
        self._chars_this_minute += len(text_chunk)
        return response.audio_content

    def _write_tags(self, flacfile, cover=False):
        f = FLAC(flacfile)

        f['albumartist'] = self._author
        f['tracknumber'] = str(self._track_number)
        f['album'] = self._album_title
        f['title'] = self._title
        f['artist'] = self._author
        f['genre'] = 'Audiobook'

        if self._coverfile:
            p = Picture()
            with open(self._coverfile, "rb") as pf:
                p.data = pf.read()
            i = Image.open(self._coverfile)
            p.width = i.width
            p.height = i.height
            p.mime = i.get_format_mimetype()
            i.close()
            p.type = id3.PictureType.COVER_FRONT
            f.add_picture(p)

        f.save()

    def text_to_flac(self, text, file_dest):
        td = TemporaryDirectory(dir='.')
        print('TMP: ' + td.name)
        for text_chunk in tqdm(text, desc=Path(file_dest).stem):
            # skip empty lines
            if text_chunk:
                success = False
                while success == False:
                    try:
                        audio_chunk = self._text_chunk_to_audio_chunk(text_chunk)
                        success = True
                    except InternalServerError:
                        continue
                wav_file_name = f'{td.name}/{str(self._chunk_counter).zfill(5)}_{Path(file_dest).with_suffix(".wav")}'
                with open(wav_file_name, 'wb') as out:
                    out.write(audio_chunk)
                with open(f'{td.name}/ffmpeg_file_list.txt', 'a', encoding='utf8') as f:
                    f.write(f'file \'{Path(wav_file_name).name}\'\n')
                self._chunk_counter += 1
        os.system(f'ffmpeg -f concat -safe 0 -i {td.name}/ffmpeg_file_list.txt -c flac "{file_dest}"')
        self._write_tags(file_dest)
