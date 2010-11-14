"""FLAC module for pyify, nearly identical to ogg"""

import os
import string
import subprocess
import util

required = { "encode": "flac",
             "decode": "flac",
             "gettags": "metaflac" }
format = "flac"

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path):
   command = ["metaflac", "--no-utf8-convert", "--export-tags-to=-", path]
   p = subprocess.Popen(command, stdout=subprocess.PIPE)

   tags = util.tagdict(p.stdout.readlines())
   p.wait()

   return tags

# return open file object with audio stream
def getAudioStream(path):
   subargv = ["flac", "-s", "-d", "-c", path]
   p = subprocess.Popen(subargv,
                        stdout=subprocess.PIPE)

   return p.stdout

def encodeAudioStream(input_stream, destination, metadata=dict()):
   encode_command = ["flac", "-f", "-s", "-8", "-", "-o", destination]
   for x in metadata.items():
      encode_command.extend(["-T", string.join(x, "=")])

   pid = util.forkexec(encode_command, file_stdin=input_stream)
   input_stream.close()

   return pid

def tagOutputFile(path, tags):
  return
