#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import sys
import getopt
import shutil
import pkgutil
import importlib

# Local imports into current namespace
from util import *

# XXX: Global.
FORMATS = dict()
queue = list()
jobs_running = 0 # XXX
encoder_pids = dict() # XXX

def process_file(path):
   basename, ext = os.path.splitext(path)
   basename = os.path.basename(path)
   if not prefs['include_dotfiles'] and basename.startswith("."):
      ify_print("Skipping %s", basename)
      return
   ext = ext[1:].lower()
   if FORMATS.has_key(ext):
      # Be more vocal about this because the user passed the file in
      # explicitly, there's more of a chance that a botched --convert-formats
      # arg was at fault.
      if not check_want_convert(ext):
         ify_warn("Skipping %s: not specified in --convert-formats!",
            os.path.basename(path))
         return 1
      destination = destination_path(path, prefs['destination'], ext)
      process_audio_file(path, destination)
   elif ext == "m3u":
      process_playlist(path)
   else:
      ify_print("Error, unsupported file format \"%s\"", ext)

def destination_path(input_file, destination, input_format):
   if prefs['filename_format'] and input_format in FORMATS:
      metadata = FORMATS[input_format].getMetadata(input_file)
      dest_name = prefs['filename_format']
      for replacement in ('title', 'artist', 'album', 'tracknumber', 'year'):
         replacement_key = replacement.upper()
         # 'YEAR' is called 'DATE' in the internal metadata format
         if replacement_key == 'YEAR':
            replacement_key = 'DATE'
         token = '%%%s%%' % replacement
         # Hack to prepend 0 to single digit track numbers
         if replacement == 'tracknumber' and len(metadata[replacement_key]) == 1:
            metadata[replacement_key] = '0' + str(metadata[replacement_key])
         if replacement_key in metadata and token in dest_name:
            dest_name = dest_name.replace(token, metadata[replacement_key])
      dest_dir = os.path.dirname(os.path.join(destination, dest_name))
      if not os.path.exists(dest_dir):
         os.makedirs(dest_dir)
      return os.path.join(destination, dest_name + "." + prefs["format"])
   else:
      basename = os.path.basename(input_file)
      return os.path.join(destination, os.path.splitext(basename)[0] + "." + prefs["format"])

def run_encode_queue():
   global jobs_running, encoder_pids

   # Start as many jobs as specified by concurrency, or as many objects
   # as there are in the queue, whichever is smaller
   for job in range(min(prefs['concurrency'], len(queue))):
      jobs_running += 1
      process_audio_file_real(*queue.pop(0))

   while jobs_running > 0:
      (pid, status) = os.waitpid(-1, os.WNOHANG)

      if pid == 0: # No changes
         time.sleep(1)
         continue

      if pid in encoder_pids:
         # Run the tag hook.
         encode_plugin = FORMATS[prefs["format"]]
         encode_plugin.tagOutputFile(*encoder_pids[pid])

         del encoder_pids[pid] # and carry on

         if len(queue) == 0: # Clean up if we're done
            jobs_running -= 1
            continue
         else: # Start a new job
            process_audio_file_real(*queue.pop(0))

def process_audio_file(from_path, to_path):
   if not prefs["force"]:
      # [6] is filesize in bytes
      if os.path.isfile(to_path) and os.stat(to_path)[6] > 0:
         ify_print(u"[up-to-date] %s", to_path)
         return

      old_ext = os.path.splitext(from_path)[1][1:]

      if old_ext == prefs["format"]:
         ify_print("[copy] %s", from_path)
         shutil.copyfile(from_path, to_path)
         return

   queue.append([from_path, to_path])

# format is already covered
def process_audio_file_real(from_path, to_path):
   '''Does no more and no less than taking the file in from_path,
      using its extension to determine its file type, and converting
      it to the format specified in the eponymous variable to the file
      specified in to_path.

      Well, it does do a little bit more - it will not overwrite an
      existing file if it's larger than 0 bytes, unless --force is
      specified. '''

   old_ext = os.path.splitext(from_path)[1][1:].lower()

   if prefs["filename_format"]:
      ify_print("[%s->%s] %s -> %s", old_ext, prefs["format"], from_path, to_path)
   else:
      ify_print("[%s->%s] %s", old_ext, prefs["format"], from_path)

   decode_plugin = FORMATS[old_ext]
   for toolCheck in ('decode', 'gettags'):
      if toolCheck in decode_plugin.required:
         for tool in decode_plugin.required[toolCheck]:
            if not in_path(tool):
               raise MissingProgramError(tool)
   for moduleCheck in ('decode_module', 'gettags_module'):
      if moduleCheck in decode_plugin.required:
         for module in decode_plugin.required[moduleCheck]:
            try:
               __import__(module)
            except ImportError:
               raise MissingModuleError(module)

   if not prefs["dry_run"]:
      encode_plugin = FORMATS[prefs["format"]]

      tags  = decode_plugin.getMetadata(from_path)
      audio = decode_plugin.getAudioStream(from_path)

      pid = encode_plugin.encodeAudioStream(audio, to_path, tags)
      encoder_pids[pid] = (to_path, tags)

   if prefs["delete"]:
      os.unlink(from_path)
      print "[deleted] %s" % from_path

def process_playlist(path):
   ify_print("[playlist]")
   print "Playlists are not yet supported!"

def process_dir(path, prefix=""):
   containing_dir = os.path.basename(path) # current toplevel path
   if not prefs['include_dotfiles'] and containing_dir.startswith("."):
      ify_print("Skipping %s", path)
      return
   target_dir = os.path.join(prefs['destination'], prefix, containing_dir)

   ify_print("[directory] %s" % target_dir)

   if not prefs["dry_run"] and not os.path.isdir(target_dir):
      os.mkdir(target_dir)

   listing = os.listdir(path)

   def sort_alpha(a, b):
      if a.lower() < b.lower():
         return -1
      elif a.lower() > b.lower():
         return 1
      else:
         return 0

   listing.sort(sort_alpha)

   for file in listing:
      file_fullpath = os.path.join(path, file)
      if os.path.isdir(file_fullpath):
         process_dir(file_fullpath, os.path.join(prefix, containing_dir))
      elif os.path.isfile(file_fullpath):
         basename, ext = os.path.splitext(file)
         ext = ext[1:].lower()
         if not prefs['include_dotfiles'] and basename.startswith("."):
            continue
         if ext in FORMATS and check_want_convert(ext):
            if prefs['filename_format']:
               destination = destination_path(file_fullpath, prefs['destination'], ext)
            else:
               destination = destination_path(file_fullpath, os.path.join(prefs['destination'],
                  prefix, containing_dir), ext)
            process_audio_file(file_fullpath, destination)

def process(arg):
   if os.path.isfile(arg):
      process_file(arg)
   elif os.path.isdir(arg):
      process_dir(arg)
   else:
      ify_print("Error: unrecognized argument \"%s\"", path)

def check_want_convert(ext):
   if prefs["convert_formats"] is None: return True
   elif ext.lower() in prefs["convert_formats"]: return True
   else: return False

# note that none of this is compatible with ify.pl
def usage():
   print """usage: ify.py [options] files
   options:
      -h or --help                  this message
      -d or --destination=PATH      path to output directory
      --filename-format             optional format for destination filename and directory.
                                    The following tags will be expanded based on each file's metadata:
                                    %album%, %artist%, %title%, %tracknumber%, %year%
      --convert-formats=FMT,FMT2..  only select files in FMT for conversion
      -o FMT or --format=FMT        convert files to this format
      -a or --include-dotfiles      include files beginning with '.' when looking for files to convert
      -f or --force                 convert even if output file is already present
      -j N                          runs N encoding jobs at once
      -q or --quiet                 don't print any output
      --delete                      delete originals after converting
      --dry-run                     don't do anything, just print actions"""
# uses gnu_getopts...there's also a realllllly nifty optparse module
# lets you specify actions, default values, argument types, etc,
# but this was easier on my brain at 12:00AM wednesday night
prefs = { 'destination': os.getcwd(),
                'convert_formats': None,
                'format': 'wav',
                'include_dotfiles': False,
                'force': False,
                'quiet': False,
                'delete': False,
                'dry_run': False,
                'filename_format': None,
                'plugin_dir': 'formats',
                'concurrency': 1 }

def main(argv):
   shortargs = "hd:o:afqj:"
   longargs  = ["help",
                "destination=",
                "filename-format=",
                "convert-formats=",
                "include-dotfiles",
                "format=",
                "force",
                "quiet",
                "delete",
                "dry-run",
                "plugin-dir="]

   opts, args = getopt.gnu_getopt(argv[1:], shortargs, longargs)

   for (option, arg) in opts:
      if option == "--help" or option == "-h":
         usage()
         sys.exit(0)
      if option == "--destination" or option == "-d":
         prefs['destination'] = arg
      elif option == '--filename-format':
         prefs['filename_format'] = arg
      elif option == "-j":
         prefs['concurrency'] = int(arg)
      elif option == "--convert-formats":
         prefs['convert_formats'] = arg.split(",")
      elif option == "--format" or option == "-o":
         prefs['format'] = arg
      elif option == "--include-dotfiles" or option == '-a':
         prefs['include_dotfiles'] = True
      elif option == "--force" or option == "-f":
         prefs['force'] = True
      elif option == "--quiet" or option == "-q":
         prefs['quiet'] = True
      elif option == "--delete" or option == "-r":
         prefs['delete'] = True
      elif option == "--dry-run":
         prefs['dry_run'] = True
      elif option == "--plugin-dir":
         if os.path.exists(arg):
            prefs['plugin_dir'] = arg
         else:
            ify_error("plugin directory does not exist")
            sys.exit(1)
   if len(args) == 0:
      raise getopt.GetoptError("No input files")
   elif False in [os.path.exists(file) for file in args]:
      print "Missing: %s" % args
      raise getopt.GetoptError("One or more input files does not exist!")

   # build FORMATS data structure
   plugin_package = __import__(prefs["plugin_dir"])
   for importer, name, ispkg in pkgutil.iter_modules(plugin_package.__path__):
      # ify_print ("Loading module %s...", name)
      plugin = importlib.import_module(plugin_package.__name__ + '.' + name)
      FORMATS[plugin.format] = plugin
   if not prefs['format'] in FORMATS:
      raise getopt.GetoptError("Format must be one of: %s" %
            ', '.join(FORMATS.keys()))
   # Now that format is validated, check that required programs are
   # available for encoding
   req = FORMATS[prefs['format']].required

   for toolCheck in ('encode',):
      if toolCheck in req:
         for tool in req[toolCheck]:
            if not in_path(tool):
               raise MissingProgramError(tool)
   for moduleCheck in ('encode_module',):
      if moduleCheck in req:
         for module in req[moduleCheck]:
            try:
               __import__(module)
            except ImportError:
               raise MissingModuleError(module)

   for arg in args:
      process(arg)

   try: run_encode_queue()
   except KeyboardInterrupt:
      for job in encoder_pids.values():
         print "[deleted] %s" % job[0]
         os.unlink(job[0])
      sys.exit(1)

if __name__ == '__main__':
   try:
      main(sys.argv)
   except getopt.GetoptError, error:
      if error.opt:
         print "Error parsing option %s: %s" % (error.opt, error.msg)
      else: 
         print "Error reading command line options: %s\n" % error.msg

      print "List of accepted arguments:"
      usage()
      sys.exit(1)
   except MissingModuleError, module:
      print 'Missing Python module: %s' % module
      print 'Install it through your package manager and try again.'
      sys.exit(1)
   except MissingProgramError, prog:
      print 'Missing encode/decode program: %s' % prog
      print 'Install it through your package manager and try again.'
      sys.exit(1)
