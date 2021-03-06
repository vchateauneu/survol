"""
Object class as defined in a software library.
"""

import cgi
import lib_util
import sys

def Graphic_colorbg():
	return "#336699"

def EntityOntology():
	return ( ["Name","File"],)

def EntityName(entity_ids_arr):
	entity_id = entity_ids_arr[0]
	# PROBLEME: Double &kt;&lt !!!
	# return entity_id
	try:
		# Trailing padding.
		resu = lib_util.Base64Decode(entity_id)
		resu = cgi.escape(resu)
		return resu
	except TypeError:
		exc = sys.exc_info()[1]
		sys.stderr.write("CANNOT DECODE: class=(%s):%s\n"%(entity_id,str(exc)))
		return entity_id

#def MakeUri(dsnName,tableNam, columnNam):
#	return lib_common.gUriGen.UriMakeFromDict("odbc/column", { "Dsn" : lib_util.EncodeUri(dsnName), "Table" : tableNam, "Column": columnNam })
#
#def AddInfo(grph,node,entity_ids_arr):
#	dsnNam = entity_ids_arr[0]
#	tabNam = entity_ids_arr[0]
#	nodeTable = odbc_table.MakeUri(dsnNam,tabNam)
#	grph.add( ( nodeTable, lib_common.MakeProp("ODBC table"), node ) )
