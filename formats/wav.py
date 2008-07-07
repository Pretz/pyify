""" Wav module for ify"""
from util import forkexec

required = dict()

format = "wav"

def getMetadata(path):
	return dict()
	
def getAudioStream(path):
	return open(path, "r")
	
def encodeAudioStream(inputStream, destination, metadata=None):
	outputStream = open(destination, "w")

	# XXX OH GOD well actually this isn't that bad but by all rights
	# we should be forking *nothing* here. the only reason this occurs
	# is to appease the job management system, which expects every
	# module to call forkexec.
	pid = forkexec(["cat"], file_stdin=inputStream, file_stdout=outputStream)
	inputStream.close()

	return pid

def tagOutputFile(path, tags):
  return
