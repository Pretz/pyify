"""ogg/vorbis module for pyify"""

import os
import string
from util import copyfileobj, forkexec

required = { "encode": "oggenc",
             "decode": "ogg123",
             "gettags": "vorbiscomment" }

format = "ogg"

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path):
	command = ["vorbiscomment", "-l", path]
	(i, o) = os.popen2(command)
	i.close()
	tags = [(x[0].upper(), unicode(x[1].strip(), 'utf-8')) for x in [elt for elt in [x.split("=", 1) for x in o.readlines()] if len(elt) == 2]]
	o.close()
	tags = dict(tags)
	return tags

# return open file object with audio stream
def getAudioStream(path):
	subargv = ["ogg123", "-d", "wav", "-q", "-f", "-", path]
	(i, o) = os.popen2(subargv, 'b')
	i.close()
	return o

def encodeAudioStream(input_stream, destination, metadata=dict()):
	encode_command = ["oggenc", "-q4.5", "-Q", "-", "-o", destination]
	
	for x in metadata.items():
		bah = string.join(x, "=")
		encode_command.extend(["-c"])
		encode_command.extend([bah])

	pid = forkexec(encode_command, file_stdin=input_stream)
	input_stream.close()

	return pid

def tagOutputFile(path, tags):
  return
