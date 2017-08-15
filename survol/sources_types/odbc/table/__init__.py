"""
Open Database Connectivity table
"""

import lib_util
import lib_common

def Graphic_colorbg():
	return "#66FF33"

def EntityOntology():
	return ( ["Dsn", "Table"], )

def MakeUri(dsnName,tableNam):
	return lib_common.gUriGen.UriMakeFromDict("odbc/table", { "Dsn" : lib_util.EncodeUri(dsnName), "Table" : tableNam })
