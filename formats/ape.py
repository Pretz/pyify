"""ape module for pyify"""

import os
import string
import subprocess
from util import forkexec, copyfileobj

required = { "encode": "mac", "decode": "mac" }
format = "ape"

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path):
	return dict()

# return open file object with audio stream
def getAudioStream(path):
	subargv = ["mac", path, "-", "-d"]
	p = subprocess.Popen(subargv,
	                     stdout=subprocess.PIPE,
	                     stderr=subprocess.PIPE,
	                     stdin=subprocess.PIPE)

	p.stderr.close()
	p.stdin.close()

	return p.stdout

def encodeAudioStream(input_stream, destination, metadata=dict()):
	# metadata is ignored because monkey's audio sucks
	encode_command = ["mac", "-", destination, "-c2000"]

	pid = forkexec(encode_command, file_stdin=input_stream)
	input_stream.close()

	return pid

def tagOutputFile(path, tags):
	return
