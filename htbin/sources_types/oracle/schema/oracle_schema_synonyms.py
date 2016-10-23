#!/usr/bin/python

"""
Oracle synonyms
"""

#import re
import sys
#import lib_common
from lib_properties import pc
import lib_oracle
import rdflib

from sources_types.oracle import schema as oracle_schema
from sources_types.oracle import synonym as oracle_synonym

def Main():
	cgiEnv = lib_oracle.OracleEnv()

	oraSchema = cgiEnv.m_entity_id_dict["Schema"]

	grph = rdflib.Graph()

	sql_query = "SELECT OBJECT_NAME,STATUS,CREATED FROM DBA_OBJECTS WHERE OBJECT_TYPE = 'SYNONYM' AND OWNER = '" + oraSchema + "'"
	sys.stderr.write("sql_query=%s\n" % sql_query )

	node_oraschema = oracle_schema.MakeUri( cgiEnv.m_oraDatabase, oraSchema )

	result = lib_oracle.ExecuteQuery( cgiEnv.ConnectStr(), sql_query)

	for row in result:
		synonymName = str(row[0])
		nodeSynonym = oracle_synonym.MakeUri( cgiEnv.m_oraDatabase , oraSchema, synonymName )
		grph.add( ( node_oraschema, pc.property_oracle_synonym, nodeSynonym ) )

		lib_oracle.AddLiteralNotNone(grph,nodeSynonym,"Status",row[1])
		lib_oracle.AddLiteralNotNone(grph,nodeSynonym,"Creation",row[2])

	# It cannot work if there are too many views.
	# cgiEnv.OutCgiRdf(grph,"LAYOUT_RECT")
	cgiEnv.OutCgiRdf(grph,"LAYOUT_RECT",[pc.property_oracle_synonym])

if __name__ == '__main__':
	Main()