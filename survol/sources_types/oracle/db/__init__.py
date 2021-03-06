"""
Oracle database
"""

import lib_common

def Graphic_colorbg():
	return "#FFCC66"


def EntityOntology():
	return ( ["Db",], )

def MakeUri(dbName):
	return lib_common.gUriGen.UriMakeFromDict("oracle/db", { "Db" : dbName } )

def EntityName(entity_ids_arr):
	return entity_ids_arr[0]

