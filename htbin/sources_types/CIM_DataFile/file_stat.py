#!/usr/bin/python

"""
File stat information
"""

# BEWARE: Do NOT rename it as stat.py otherwise strange errors happen,
# probably a collision of modules names, with the message:
# "Fatal Python error: Py_Initialize: can't initialize sys standard streams"

import os
import sys
import time
import rdflib
import psutil
import json
from sources_types import CIM_DataFile
import lib_util
import lib_common
import lib_properties
from lib_properties import pc
import mimetypes # In Python standard library.

try:
	import win32api
	import lib_win32
	FilNamToProperties = lib_win32.getFileProperties
except ImportError:
	def FilNamToProperties(filNam):
		return {}

def Main():
	cgiEnv = lib_common.CgiEnv()
	filNam = cgiEnv.GetId()
	sys.stderr.write("filNam=%s\n" % filNam )

	filNode = lib_common.gUriGen.FileUri(filNam )

	grph = rdflib.Graph()

	try:
		info = os.stat(filNam)
	except Exception:
		# On recent Python versions, we would catch IOError or FileNotFoundError.
		exc = sys.exc_info()[1]
		lib_common.ErrorMessageHtml("Caught:"+str(exc))
	except IOError:
		lib_common.ErrorMessageHtml("IOError:"+filNam)
	except FileNotFoundError:
		lib_common.ErrorMessageHtml("File not found:"+filNam)
	except PermissionError:
		lib_common.ErrorMessageHtml("Permission error:"+filNam)
	except OSError:
		lib_common.ErrorMessageHtml("Incorrect syntax:"+filNam)

	# st_mode: protection bits.
	# st_ino: inode number.

	# st_dev: device.
	deviceName = "Device:"+str(info.st_dev)
	if lib_util.isPlatformLinux:
		# TODO: How to get the device name on Windows ???
		for line in file('/proc/mounts'):
			# lines are device, mountpoint, filesystem, <rest>
			# later entries override earlier ones
			line = [s.decode('string_escape') for s in line.split()[:3]]
			try:
				if os.lstat(line[1]).st_dev == info.st_dev:
					deviceName = line[1]
					break
			except OSError:
				# Beware, index 1, not 0:
				# "[Errno 13] Permission denied: '/run/user/42/gvfs'"
				# Better display the error message.
				exc = sys.exc_info()[1]
				deviceName=str(exc)
				break

		deviceNode = lib_common.gUriGen.DiskPartitionUri(deviceName)
		grph.add( ( filNode, pc.property_file_device, deviceNode ) )

	CIM_DataFile.AddStatNode( grph, filNode, info )
	CIM_DataFile.AddMagic( grph, filNode, filNam )

	# st_nlink: number of hard links.

	# st_uid: user id of owner.
	try:
		# Can work on Unix only.
		import pwd
		user = pwd.getpwuid( info.st_uid )
		userName = user[0]
		userNode = lib_common.gUriGen.UserUri(userName)
		grph.add( ( filNode, pc.property_owner, userNode ) )
	except ImportError:
		pass

	# st_gid: group id of owner.
	try:
		# Can work on Unix only.
		import grp
		group = grp.getgrgid( info.st_gid )
		groupName = group[0]
		groupNode = lib_common.gUriGen.GroupUri(groupName)
		grph.add( ( filNode, pc.property_group, groupNode ) )
	except ImportError:
		pass

	# Displays the file and the parent directories/
	currFilNam = filNam
	currNode = filNode
	while True:
		dirPath = os.path.dirname( currFilNam )
		if dirPath == currFilNam:
			break
		if dirPath == "":
			break
		dirNode = lib_common.gUriGen.FileUri( dirPath )
		grph.add( ( dirNode, pc.property_directory, currNode ) )
		sys.stderr.write("dirPath=%s\n" % dirPath)
		statPath = os.stat(dirPath)
		CIM_DataFile.AddStatNode( grph, dirNode, statPath )


		propDict = FilNamToProperties(currFilNam)
		for prp, val in propDict.items():
			val = propDict[prp]
			if val is None:
				continue

			if isinstance( val, dict ):
				# val = ", ".join( "%s=%s" % (k,val[k]) for k in val )
				val = json.dumps(val)
				# TODO: Unicode error encoding=ascii
				# 169	251	A9	10101001	"Copyright"	&#169;	&copy;	Copyright sign
				# Might contain this: "LegalCopyright Copyright \u00a9 2010"
				val = val.replace("\\","\\\\")
			grph.add( ( currNode, lib_properties.MakeProp(prp), rdflib.Literal(val) ) )

		mimTy = mimetypes.guess_type(currFilNam)
		if mimTy:
			if mimTy[0]:
				grph.add( ( currNode, lib_properties.MakeProp("Mime type"), rdflib.Literal(str(mimTy)) ) )

		currFilNam = dirPath
		currNode = dirNode


	# If windows, print more information: DLL version etc...
	# http://stackoverflow.com/questions/580924/python-windows-file-version-attribute

	# cgiEnv.OutCgiRdf(grph)
	cgiEnv.OutCgiRdf(grph,"LAYOUT_TWOPI")

if __name__ == '__main__':
	Main()