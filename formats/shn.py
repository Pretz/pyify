"""shn module for pyify"""

import os
import string
import popen2
#from util import copyfileobj
from util import forkexec, copyfileobj

required = { "encode": "shorten", "decode": "shorten" }
format = "shn"

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path):
	return dict()

# return open file object with audio stream
def getAudioStream(path):
	subargv = ["shorten", "-x", path, "-"]
	(o, i, e) = os.popen3(subargv, 'b')
	o.close()
	e.close()
	return i

def encodeAudioStream(input_stream, destination, metadata=dict()):
	# metadata is ignored because monkey's audio sucks
	encode_command = ["shorten", "-", destination]
	
	pid = forkexec(encode_command, file_stdin=input_stream)
	input_stream.close()

	return pid

def tagOutputFile(path, tags):
  return
