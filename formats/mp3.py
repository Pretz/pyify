"""mp3 module for pyify"""

import os
import string
import sys
import subprocess
from util import forkexec

required = {
  "encode": ["lame"],
  "decode": ["mpg321"],
  "encode_module": ["eyeD3"],
}

format = "mp3"

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path):
   import eyeD3

   tag = eyeD3.Tag()
   tag.link(path)

   tags = { 'ARTIST': tag.getArtist(),
      'ALBUM': tag.getAlbum(),
      'TITLE': tag.getTitle(),
      'DATE': tag.getYear() }

   if tag.getGenre() is not None:
      tags['GENRE'] = tag.getGenre().getName()

   if tag.getTrackNum()[0] is not None:
      tags['TRACKNUMBER'] = str(tag.getTrackNum()[0])

   for name in tags.keys():
      if tags[name] is None or len(tags[name]) == 0:
         del tags[name]

   return tags

# return open file object with audio stream
def getAudioStream(path):
   subargv = ["mpg321", "-q", "-w", "-", path]
   p = subprocess.Popen(subargv, stdout=subprocess.PIPE)
   return p.stdout

def encodeAudioStream(input_stream, destination, metadata=dict()):
   encode_command = ["lame", "-V0", "--quiet", "--vbr-new", '-', destination]

   pid = forkexec(encode_command, file_stdin=input_stream)
   input_stream.close()

   return pid

def tagOutputFile(path, tags):
   import eyeD3

   tag_bind = {
      'ARTIST': 'TPE1',
      'TITLE': 'TIT2',
      'ALBUM': 'TALB',
      'DATE': 'TYER',
      'TRACKNUMBER': 'TRCK'
   }

   tag = eyeD3.Tag()
   tag.link(path)
   tag.header.setVersion(eyeD3.ID3_V2_4)
   tag.setTextEncoding(eyeD3.UTF_8_ENCODING)

   for key, flag in tag_bind.items():
      if key in tags:
         tag.setTextFrame(flag, tags[key])

   if 'ALBUM_ARTIST' in tags:
      tag.setTextFrame("TPE2", tags['ALBUM_ARTIST'])
   elif 'ARTIST' in tags:
      tag.setTextFrame("TPE2", tags['ARTIST'])

   if 'GENRE' in tags:
      try: tag.setGenre(tags['GENRE'].encode('ascii'))
      except: print "Warning: Genre '%s' not understood by eyeD3" % tags['GENRE']

   tag.update()

   return
