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

   # XXX: We do this only because the job management system expects every
   # module to return a process ID for encoding. In a perfect world, we should
   # be forking *nothing* here, and returning a file object instead.
   pid = forkexec(["cat"], file_stdin=inputStream, file_stdout=outputStream)
   inputStream.close()

   return pid

def tagOutputFile(path, tags):
   return
