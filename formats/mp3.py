"""mp3 module for pyify"""

import os
import string
import popen2
import sys
from util import forkexec, copyfileobj

required = { "encode": "lame", "decode": "mpg123" }
format = "mp3"

# return a dictionary file of the metadata
# key names are based on output of vorbiscomment
def getMetadata(path):
	try: import eyeD3
	except:
		sys.stderr.write("Warning: no ID3 support, please install python-eyed3")
		return dict()
	
	tag = eyeD3.Tag()
	tag.link(path)

	tags = { 'ARTIST': tag.getArtist(),
		'ALBUM': tag.getAlbum(),
		'TITLE': tag.getTitle(),
		'DATE': tag.getYear() }

	if tag.getGenre() != None:
		print tag.getGenre().getName()
		tags['GENRE'] = tag.getGenre().getName()

	if tag.getTrackNum() != None:
		tags['TRACKNUMBER'] = str(tag.getTrackNum()[0])

	for tag in tags:
		if tag[1] == "" or tag[1] == None:
			del tags[tag[0]]

	return tags

# return open file object with audio stream
def getAudioStream(path):
	subargv = ["mpg123", "-q", "-s", path]
	(i, o) = os.popen2(subargv, 'b')
	i.close()
	return o

def encodeAudioStream(input_stream, destination, metadata=dict()):
	encode_command = ["lame", "-V5", "--quiet", "--vbr-new", '-', destination]

	pid = forkexec(encode_command, file_stdin=input_stream)
	input_stream.close()

	return pid

def tagOutputFile(path, tags):
	tag_bind = { 'ARTIST': 'TPE1', 
				 'TITLE': 'TIT2', 
				 'ALBUM': 'TALB',
				 'DATE': 'TYER',
				 'TRACKNUMBER': 'TRCK' }

	try: import eyeD3
	except:
		print "Can't tag! Install python-eyed3."
		return

	tag = eyeD3.Tag()
	tag.link(path)
	tag.header.setVersion(eyeD3.ID3_V2_4)
	tag.setTextEncoding(eyeD3.UTF_8_ENCODING)

	for key, flag in tag_bind.items():
		if key in tags:
			tag.setTextFrame(flag, tags[key])

	if 'ALBUM_ARTIST' in tags:
		tag.setTextFrame("TPE2", tags['ALBUM_ARTIST'])
	elif 'ARTIST' in tags:
		tag.setTextFrame("TPE2", tags['ARTIST'])

	if 'GENRE' in tags:
		try: tag.setGenre(tags['GENRE'].encode('ascii'))
		except: print "Warning: Genre '%s' not understood by eyeD3" % tags['GENRE']

	tag.update()

	return