import argparse
import getopt
import ify
import os
import sys
import time
from util import MissingModuleError, MissingProgramError
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class IfyEventHandler(PatternMatchingEventHandler):

   def __init__(self, extensions, ify_args):
      self.ify_args = ify_args
      patterns = ['*.' + extension for extension in extensions]
      super(IfyEventHandler, self).__init__(patterns, ignore_directories=True)
      print "Watching for extensions %s" % patterns

   def on_created(self, event):
      self.wait_to_process(event.src_path)

   def on_moved(self, event):
      self.wait_to_process(event.dest_path)

   def wait_to_process(self, path):
      print "Waiting to process %s" % path
      """Waits until the file at path doesn't change for a whole second before passing
      it to ify for processing; this ensures files still being written to aren't
      transcoded."""
      stat = os.stat(path)
      time_slept = 0
      while True:
         time.sleep(1)
         time_slept += 1
         newstat = os.stat(path)
         # Wait 30 seconds for a file of size zero to be initialized
         if newstat.st_size == 0 and time_slept < 30:
            continue
         if stat.st_size == newstat.st_size and stat.st_mtime == newstat.st_mtime:
            break
         stat = newstat
      self.process_file(path)

   def process_file(self, path):
      print "Running ify: %s" % (self.ify_args + [path])
      run_ify(['watcher'] + self.ify_args + [path])


def run_ify(args):
   try:
      ify.main(args)
   except getopt.GetoptError, error:
      if error.opt:
         print "Error parsing option %s: %s" % (error.opt, error.msg)
      else:
         print "Error reading command line options: %s\n" % error.msg
      print "List of accepted arguments:"
      ify.usage()
      sys.exit(1)
   except MissingModuleError, module:
      print 'Missing Python module: %s' % module
      print 'Install it through your package manager and try again.'
      sys.exit(1)
   except MissingProgramError, prog:
      print 'Missing encode/decode program: %s' % prog
      print 'Install it through your package manager and try again.'
      sys.exit(1)


def observe(watch_path, watch_extensions, ify_arguments):
   handler = IfyEventHandler(watch_extensions, ify_arguments)
   observer = Observer()
   observer.schedule(handler, path=watch_path, recursive=True)
   observer.start()
   try:
      while True:
         time.sleep(1)
   except KeyboardInterrupt:
      observer.stop()
   observer.join()


if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Watch a directory hierarchy and invoke ify when new files are created.')
   parser.add_argument('watch-dir', type=str, help='directory to watch for changes')
   parser.add_argument('-e', '--extensions', type=str, help='extensions to watch for changes, separated by commas e.g. mp3,flac,m4a,ogg')
   parser.add_argument('ify-arguments', type=str, nargs=argparse.REMAINDER, help='arguments to pass to ify for each file')
   args = vars(parser.parse_args())
   extensions = args['extensions'].split(',')
   observe(args['watch-dir'], extensions, args['ify-arguments'])

