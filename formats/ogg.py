"""ogg/vorbis module for pyify"""

import os
import string
import subprocess
from util import copyfileobj, forkexec, tagdict

required = { "encode": "oggenc",
             "decode": "ogg123",
             "gettags": "vorbiscomment" }

format = "ogg"

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path):
   command = ["vorbiscomment", "-l", path]
   p = subprocess.Popen(command, stdout=subprocess.PIPE)
   tags = util.tagdict(p.stdout.readlines())
   p.wait()

   return tags

# return open file object with audio stream
def getAudioStream(path):
   subargv = ["ogg123", "-d", "wav", "-q", "-f", "-", path]
   p = subprocess.Popen(subargv, stdout=subprocess.PIPE)
   return p.stdout

def encodeAudioStream(input_stream, destination, metadata=dict()):
   encode_command = ["oggenc", "-q4.5", "-Q", "-", "-o", destination]

   for keyval in metadata.items():
      tag = string.join(keyval, "=")
      encode_command.extend(["-c"])
      encode_command.extend([tag])

   pid = forkexec(encode_command, file_stdin=input_stream)
   input_stream.close()

   return pid

def tagOutputFile(path, tags):
  return
