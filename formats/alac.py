"""apple lossless module for pyify"""

import subprocess
import sys
from util import forkexec

required = {
  "encode": ["ffmpeg"],
  "decode": ["ffmpeg"]
}
format = "m4a"

mapping = {
  '\xa9alb': 'ALBUM',
  '\xa9nam': 'TITLE',
  '\xa9ART': 'ARTIST',
  '\xa9day': 'DATE',
  '\xa9cmt': 'description', 
  '\xa9too': 'encoded-by',
     # 'cpil': 'compilation',  # TODO: Do other file formats have a compilation tag? Useful for iTunes sorting
  # '\xa9wrt': 'performer',
     'trkn': 'TRACKNUMBER',
  '\xa9gen': 'GENRE',
     'disk': 'discnumber'
}

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path, _=None):
  try: from mutagen.mp4 import MP4
  except:
    sys.stderr.write("Warning: no MP4 support, please install mutagen")
    return dict()
  track = MP4(path)
  tags = {}
  
  for key in mapping:
    if key in track:
      destkey = mapping[key]
      tags[destkey] = track[key][0]
      if isinstance(tags[destkey], tuple) or isinstance(tags[destkey], list):
        tags[destkey] = str(tags[mapping[key]][0])
      if destkey == "DATE":
        tags[destkey] = tags[destkey].split("-")[0]

  return tags

# return open file object with audio stream
def getAudioStream(path):
  subargv = ["ffmpeg", "-v", "1", "-i", path, "-f", "wav", "-"]
  p = subprocess.Popen(subargv, stdout=subprocess.PIPE)
  return p.stdout

def encodeAudioStream(input_stream, destination, metadata=dict()):
  encode_command = ["ffmpeg", "-v", "1", "-i", "-", "-acodec", "alac", destination]

  pid = forkexec(encode_command, file_stdin=input_stream)
  input_stream.close()

  return pid

def tagOutputFile(path, tags):
  
  try: from mutagen.mp4 import MP4
  except:
    print "Can't tag! Install mutagen."
    return

  track = MP4(path)
  for key, flag in mapping.iteritems():
    if flag == 'TRACKNUMBER':
      trackinfo = tags[flag].split("/")
      if len(trackinfo) > 1:
        trackno = trackinfo[0]
        diskno = trackinfo[1]
      else:
        trackno = trackinfo[0]
        diskno = None
      track[key] = [(int(trackno), 0)]
      if diskno:
        track['disk'] = [(int(diskno), 0)]
    elif flag in tags:
      track[key] = tags[flag]
  track.save()

  return
