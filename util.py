from os import fork, wait, execvp, pipe, dup2, setpgrp, environ
import os.path
import sys
import hashlib

class MissingProgramError(Exception):
   pass

class MissingModuleError(Exception):
   pass

# Yoinked from Christopher Lenz at
# http://bitten.cmlenz.net/browser/trunk/bitten/util/md5sum.py
def getchecksum(filename):
   """Generate an MD5 checksum for the specified file.

      @param filename: the absolute path to the file
      @return: string containing the checksum
   """
   checksum = hashlib.new("md5")
   fileobj = file(filename, 'rb')
   try:
      while True:
         chunk = fileobj.read(4096)
         if not chunk:
            break
         checksum.update(chunk)
   finally:
      fileobj.close()
   return checksum.hexdigest()

# Turn an iterable of lines like
# ARTIST=Foo
# ALBUM=Bar
# into a dict {'ARTIST':'Foo', 'ALBUM':'Bar'}
# It does unicode for the values, and normalizes the LHS (tag name) to
# uppercase.
def tagdict(lines):
   ret = {}
   for line in lines:
      (key, value) = line.rstrip().split('=', 1)
      if key is not None and value is not None:
         ret[key.upper()] = unicode(value, 'utf-8')
   return ret

# execute child process which will optionally use
# either stdin as it's standard input or stdout as its
# standard output or both
def forkexec(args, file_stdin=None, file_stdout=None):
   pid = fork()
   if pid == 0:
      if file_stdin:
         dup2(file_stdin.fileno(), sys.stdin.fileno())
         os.close(file_stdin.fileno())
      if file_stdout:
         dup2(file_stdout.fileno(), sys.stdout.fileno())
         os.close(file_stdout.fileno())
      execvp(args[0], args)
   elif pid > 0:
      return pid # ignored right now

#replacement for shutil.copyfileobj that works
def copyfileobj(src, dst):
   while True:
      buf = src.read(4096)
      if len(buf) > 0: dst.write(buf)
      else: return
      if len(buf) < 4096: return

def in_path(file):
   path = environ["PATH"].split(":")
   for pathelt in path:
      if os.path.exists(os.path.join(os.path.expanduser(pathelt), file)):
         return True
   return False

# we have a global being defined here in util.py...is this bad idea?
quiet = False
def ify_print(message, *args):
   if not quiet:
      print message % tuple(args)

def ify_warn(message, *args):
   sys.stderr.write("Warning: ")
   sys.stderr.write(message % tuple(args))
   sys.stderr.write("\n")

def ify_error(message, *args):
   sys.stderr.write("Error: ")
   sys.stderr.write(message % tuple(args))
   sys.stderr.write("\n")
