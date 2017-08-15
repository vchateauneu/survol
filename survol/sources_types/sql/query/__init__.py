import re
import sys
import cgi
import lib_util
import lib_common

# This array will be concatenated to other strings, depending of the origin of the query: database,
# process memory, file content.
def EntityOntology():
	return ( ["Query",], )

# The SQL query is encoded in base 64 because it contains many special characters which would be too complicated to
# encode as HTML entities. This is not visible as EntityName() does the reverse decoding.
# TODO: This is called from other classes like that: sql_query.MakeUri( strQuery, "oracle/query", Db = theDb )
# On voudrait davantage generaliser.
def MakeUri(strQuery,derivedEntity = "sql/query", **kwargs):
	# sys.stderr.write("derivedEntity=%s strQuery=%s kwargs=%s\n"%(derivedEntity,strQuery,str(kwargs)))
	strQueryEncoded = lib_util.Base64Encode(strQuery)
	# The result might be: { "Query" : strQueryEncoded, "Pid" : thePid  }
	allKeyedArgs = { "Query" : strQueryEncoded }
	allKeyedArgs.update( kwargs )
	# Maybe we could take the calling module as derived entity ?
	return lib_common.gUriGen.UriMakeFromDict(derivedEntity,allKeyedArgs )

def AddInfo(grph,node,entity_ids_arr):
	strQuery = entity_ids_arr[0]

# TODO: It should not strip blanks between simple-quotes.
def stripblanks(text):
	lst = text.split('"')
	for i, item in enumerate(lst):
		if not i % 2:
			lst[i] = re.sub("\s+", " ", item)
	return '"'.join(lst)

# This is dynamically called from the function EntityArrToLabel() in lib_naming.py.
# It returns a printable string, given the url arguments.
# Probleme: Ce n est pas compatible avec des arguments variables.
def EntityName(entity_ids_arr,entity_host):
	resu = lib_util.Base64Decode(entity_ids_arr[0])
	resu = cgi.escape(resu)
	resu = stripblanks(resu)
	return resu

# This extracts the arguments from the URL. We make a function from it so that
# it wraps the decoding.
def GetEnvArgs(cgiEnv):
	sqlQuery_encode = cgiEnv.m_entity_id_dict["Query"]
	sqlQuery = lib_util.Base64Decode(sqlQuery_encode)
	return ( sqlQuery )



def EntityNameUtil(textPrefix,sqlQuery):
	resu = lib_util.Base64Decode(sqlQuery)
	resu = cgi.escape(resu)
	resu = stripblanks(resu)

	lenFilNam = len(textPrefix)
	lenResu = len(resu)
	lenTot = lenFilNam + lenResu
	lenMaxi = 50
	lenDiff = lenTot - lenMaxi
	if lenDiff > 0:
		lenResu -= lenDiff
		if lenResu < 30:
			lenResu = 30

		return textPrefix + ":" + resu[:lenResu] + "..."
	else:
		return textPrefix + ":" + resu