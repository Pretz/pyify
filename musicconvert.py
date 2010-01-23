#!/usr/bin/env python
import os, os.path
import sys
import re
from optparse import OptionParser
import ify

SUPPORTED_EXTS = ["mp3", "ogg", "mp4", "flac", "m4a"]
RestrictedCharPattern = re.compile('[\\\\/:\*\?"<>\|]')

usage = "usage: %prog [options] sourcedirectory targetdirectory"
parser = OptionParser(usage=usage)
parser.add_option("-f", "--format", default="mp3",
                  help="target output format")
parser.add_option("-o", "--output", 
                  help="root folder to output files to")
parser.add_option("-q", "--quiet", default=False,
                  help="don't print status messages to stdout")

(options, args) = parser.parse_args()

def pathescape(str):
  return re.sub(RestrictedCharPattern, "_", str)

def convert_directory(directory):
  for root, dirs, files in os.walk(directory):
    for file in files:
      extension = os.path.splitext(file)[1][1:].lower()
      if (extension in SUPPORTED_EXTS):
        format = extension
        if (extension in ["mp4", "m4a"]):
          format = "alac"
        converter = __import__("formats.%s" % format).__dict__[format]
        try:
          tags = converter.getMetadata(os.path.join(root, file))
        except: # Skip files w/ bad metadate
          print >>sys.stderr, "Skipping %s, unreadable tags, dir: %s" % (file, root)
          continue
        fileDest = os.path.join(options.output, pathescape(tags["ARTIST"]), pathescape(tags["ALBUM"]),\
         "%s - %s.%s" % (pathescape(tags["TRACKNUMBER"]), pathescape(tags["TITLE"]), options.format))
        print fileDest
        if not os.path.exists(os.path.dirname(fileDest)):
          os.makedirs(os.path.dirname(fileDest))
        ify.process_audio_file(os.path.join(root, file), fileDest)

ify.load_plugins()
ify.prefs['format'] = options.format
for dir in args:
  convert_directory(dir)
ify.run_encode_queue()