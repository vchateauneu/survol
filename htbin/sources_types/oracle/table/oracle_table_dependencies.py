#!/usr/bin/python

"""
Oracle table dependencies
"""

import re
import sys
import lib_common
from lib_properties import pc
import lib_oracle
import rdflib

def Main():
	cgiEnv = lib_oracle.OracleEnv()

	oraTable = cgiEnv.m_entity_id_dict["Table"]
	oraSchema = cgiEnv.m_entity_id_dict["Schema"]
	oraDatabase = cgiEnv.m_entity_id_dict["Db"]

	grph = rdflib.Graph()

	# TYPE = "VIEW", "TABLE", "PACKAGE BODY" etc...
	sql_query = "select owner,name,type from dba_dependencies where REFERENCED_TYPE = 'TABLE' AND REFERENCED_NAME = '" + oraTable + "' and referenced_owner='" + oraSchema + "'"

	sys.stderr.write("sql_query=%s\n" % sql_query )

	node_oraTable = lib_common.gUriGen.OracleTableUri( oraDatabase, oraSchema, oraTable )

	node_oraSchema = lib_common.gUriGen.OracleSchemaUri( oraDatabase, oraSchema )
	grph.add( ( node_oraSchema, pc.property_oracle_table, node_oraTable ) )

	result = lib_oracle.ExecuteQuery( cgiEnv.ConnectStr(), sql_query)

	for row in result:
		lib_oracle.AddDependency( grph, row, node_oraTable, oraDatabase, True )

	cgiEnv.OutCgiRdf(grph,"LAYOUT_RECT")
if __name__ == '__main__':
	Main()
