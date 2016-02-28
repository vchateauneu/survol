
import socket
import urllib
import psutil

try:
    import simplejson as json
except ImportError:
    import json

# In Python 3, urllib.quote has been moved to urllib.parse.quote and it does handle unicode by default.
# Consider using module "six".
try:
	from urllib import unquote
	from urlparse import urlparse
except ImportError:
	from urllib.parse import unquote
	from urllib.parse import urlparse


try:
	# Python 3
	from urllib import HTTPError
except ImportError:
	# from urllib.error import HTTPError
	pass

import threading
import signal
import sys
import cgi
import cgitb
import os
import re
import time

import lib_util
import lib_patterns
import lib_properties
import lib_naming
from lib_properties import pc
from lib_properties import MakeProp

import collections
import rdflib

# Functions for creating uris are imported in the global namespace.
from lib_uris import *
import lib_uris
# globals()["gUriGen"] = lib_uris.gUriGen

################################################################################


# "http://primhillcomputers.com/ontologies/smbshare" = > "smbshare"
def AntiPredicateUri(uri):
	return uri[ len(lib_properties.primns_slash) : ]

################################################################################

def TimeStamp():
	return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

################################################################################

# Apache http://127.0.0.1/PythonStyle/htbin/internals/print.py
# Entity http://127.0.0.1/PythonStyle/htbin/entity.py
# SCRIPT_NAME=/PythonStyle/htbin/internals/print.py
# REMOTE_ADDR=127.0.0.1
# SERVER_PORT=80
# SCRIPT_FILENAME=D:/Projects/Divers/Reverse/PythonStyle/htbin/internals/print.py
# REQUEST_URI=/PythonStyle/htbin/internals/print.py
#
# Script http://127.0.0.1:8000/htbin/internals/print.py
# Entity http://127.0.0.1:8000/htbin/entity.py
# REMOTE_ADDR=127.0.0.1
# SERVER_PORT=8000
# SCRIPT_NAME=/htbin/internals/print.py
# PATH_TRANSLATED=D:\Projects\Divers\Reverse\PythonStyle
def PathRoot():
	# TODO: Check that it returns also the path, on all platforms.
	scriptFilNam = __file__

	idx = scriptFilNam.find('htbin')
	root = scriptFilNam[:idx] + 'htbin'
	return root

pathRoot = PathRoot()

################################################################################

# Adds a key value pair at the end of the url with the right delimiter.
# TODO: Checks that the argument is not already there.
# TODO: Most of times, it is used for changing the mode.
def ConcatenateCgi(url,keyvalpair):
	if url.rfind( '?' ) == -1:
		return url + "?" + keyvalpair
	else:
		return url + "&" + keyvalpair


################################################################################

# This is used to call an URL with mode=info as CGI argument. The url returns
# a Json array describing this URL, for example the title.
# TODO: As this information rarely changes, it can be cached in a text file.
infoContentType = "application/json"

def SerialiseScriptInfo(pairs):
	strJson = json.dumps(pairs)
	lib_util.HttpHeader( sys.stdout, infoContentType )
	sys.stderr.write("strJson=%s\n" % strJson )
	print(strJson)

# Used for displaying information about scripts.
# This function must never fail even if the url is broken
# or returns wrong data.
def DeserializeScriptInfo(urlScript):
	# TODO: Consider using ModedUrl("edit")
	urlModeInfo = ConcatenateCgi( urlScript, "mode=info" )
	sys.stderr.write("DeserializeScriptInfo:%s\n" % (urlModeInfo) )
	# Changed in version 2.6: timeout was added.
	if sys.version_info >= (2,6):
		try:
			response = urlopen(urlModeInfo,data=None,timeout=3)
		except socket.timeout:
			return { "info" : "Time-out", "Status" : False }
		# Not accepted on Python 2.7 and Windows.
		#except urllib.error.HTTPError:
		#	exc = sys.exc_info()[1]
		#	# It can be any error but we do not want to be stuck.
		#	return { "info" : "Warning:" + str(exc), "Status" : False }
		# It can be "URLError" on Python 3.4 on Windows XP
		except Exception:
			exc = sys.exc_info()[1]
			return { "info" : str(exc), "Status" : False }
	else:
		response = urlopen(urlModeInfo)

	url_info = response.info()
	contentType = url_info['content-type']
	if contentType != infoContentType:
		return { "info" : "Unexpected error", "Status" : False }

	content = response.read()
	return json.loads( content.decode() )

################################################################################

# Here, should create a connection to the hostname.
def AnonymousPidNode(host):
	return rdflib.BNode()

nodeMachine = gUriGen.HostnameUri( lib_util.currentHostname )

################################################################################

# This applies to Linux and KDE only. Temporary.
# We want to avoid too many processes to display, when debugging.
# Could be reused if we want to focus on some processes only.
uselessProcesses = [ 'bash', 'gvim', 'konsole' ]

def UselessProc(proc):
	if lib_util.isPlatformWindows:
		return False
	else:
		return proc.name in uselessProcesses

################################################################################
	
## Also, the Apache 2.2 docs have a slightly different location for the registry key:
## HKEY_CLASSES_ROOT\.cgi\Shell\ExecCGI\Command\(Default) => C:\Perl\bin\perl.exe -wT

################################################################################

maxHtmlTitleLen = 50
withBrDelim = '<BR ALIGN="LEFT" />'

# Inserts "<BR/>" in a HTML string so it is wrapped in a HTML label.
def StrWithBr(str):
	lenStr = len(str)
	if lenStr < maxHtmlTitleLen:
		return str

	splt = str.split(" ")
	totLen = 0
	resu = ""
	currLine = ""
	for currStr in splt:
		subLen = len(currStr)
		if totLen + subLen < maxHtmlTitleLen:
			currLine += " " + currStr
			totLen += subLen
			continue
		if resu:
			resu += withBrDelim
		resu += currLine
		currLine = currStr
		totLen = subLen

	if currLine:
		if resu != "":
			resu += withBrDelim
		resu += currLine
	return resu

################################################################################

# TODO: Set the right criteria for an old Graphviz version.
new_graphiz = True # sys.version_info >= (3,)

# This is temporary because only old graphviz versions dot not implement that.
def DotBold(str):
	return "<b>%s</b>" % str if new_graphiz else str

def DotUL(str):
	return "<u>%s</u>" % str if new_graphiz else str

################################################################################

# Static data for dot conversion.
# Taken from rdf2dot, in module rdflib.

EDGECOLOR = "blue"
NODECOLOR = "black"
ISACOLOR = "black"

# TODO: Add a tool tip. Also, adapt the color to the context.
pattEdgeOrien = "\t%s -> %s [ color=%s, label=< <font point-size='10' " + \
	"color='#336633'>%s</font> > ] ;\n"
pattEdgeBiDir = "\t%s -> %s [ dir=both color=%s, label=< <font point-size='10' " + \
	"color='#336633'>%s</font> > ] ;\n"

################################################################################

def WriteDotHeader( page_title, layout_style, stream, grph ):
	# Title embedded in the page.
	stream.write('digraph "' + page_title + '" { \n')

	# CSS style-sheet should be in the top-level directory ?
	# Not implemented in 2010: http://graphviz.org/bugs/b1874.html
	# Add a CSS-like "class" attribute
	# stream.write(' stylesheet = "rdfmon.css" \n')

	# Maybe the layout is forced.
	# dot - "hierarchical" or layered drawings of directed graphs. This is the default tool to use if edges have directionality.
	# neato - "spring model'' layouts.  This is the default tool to use if the graph is not too large (about 100 nodes) and you don't know anything else about it. Neato attempts to minimize a global energy function, which is equivalent to statistical multi-dimensional scaling.
	# fdp - "spring model'' layouts similar to those of neato, but does this by reducing forces rather than working with energy.
	# sfdp - multiscale version of fdp for the layout of large graphs.
	# twopi - radial layouts, after Graham Wills 97. Nodes are placed on concentric circles depending their distance from a given root node.
	# circo - circular layout, after Six and Tollis 99, Kauffman and Wiese 02. This is suitable for certain diagrams of multiple cyclic structures, such as certain telecommunications networks.
	# This is a style more than a dot layout.
	sys.stderr.write("Lay=%s\n" % (layout_style) )
	if layout_style == "LAYOUT_RECT":
		dot_layout = "dot"
		# Very long lists: Or very flat tree.
		stream.write(" splines=\"ortho\"; \n")
		stream.write(" rankdir=\"LR\"; \n")
	elif layout_style == "LAYOUT_TWOPI":
		# Used specifically for file/file_stat.py : The subdirectories
		# are vertically stacked.
		dot_layout = "twopi"
	elif layout_style == "LAYOUT_XXXX":
		# Used specifically for modules dependencies on Linux,
		# which have about 5000 nodes. fdp and neato are far too slow,
		# and the result is not readable.
		dot_layout = "twopi"
		# Very long lists: Or very flat tree.
		# stream.write(" layout=\"dot\"; \n")
		# stream.write(" splines=\"ortho\"; \n")
		# stream.write(" rankdir=\"LR\"; \n")
	elif layout_style == "LAYOUT_SPLINE":
		# Win32_Services, many interconnections.
		dot_layout = "fdp"
		# stream.write(" splines=\"curved\"; \n") # About as fast as straight lines
		stream.write(" splines=\"spline\"; \n") # Slower than "curved" but acceptable.
		# stream.write(" splines=\"compound\"; \n") ### TRES LENT
	else:
		dot_layout = "fdp" # Faster than "dot"
		# TODO: Maybe we could use the number of elements len(grph)  ?
	stream.write(" layout=\"" + dot_layout + "\"; \n")

	stream.write(" node [ fontname=\"DejaVu Sans\" ] ; \n")
	return dot_layout

# This is very primitive and maybe should be replaced by a standard function,
# but lib_util.EncodeUri() replaces "too much", and SVG urls cannot encode an ampersand...
# The problems comes from "&mode=edit" or "&mode=html" etc...
# TODO: If we can fix this, then "xid" can be replaced by "entity_type/entity_id"
def UrlToSvg(url):
	if lib_util.isPlatformWindows:
		# If one ampersand only, "error on line 28 at column 75: EntityRef: expecting ';'"
		# when displaying the SVG file.
		# Windows, Python 3.2, Graphviz 2.36
		return url.replace( "&", "&amp;amp;" )
	else:
		if sys.version_info <= (2,5):
			# Linux, Python 2.5.  Tested on Mandriva.
			# Maybe we should do the same as the others.
			return url.replace( "&", "&amp;" )
		else:
			# Tested with Python 2.7 on Fedora.
			return url.replace( "&", "&amp;amp;" )

def WriteDotLegend( page_title, topUrl, errMsg, isSubServer, parameters, stream, grph ):

	# TODO: HOW COULD WE EDIT THE PARAMETERS IN THE SVG DOCUMENT ???????

	# TODO: Lettre Info pour topUrl.

	stream.write("""
  rank=sink;
  rankdir=LR
  node [shape=plaintext]
 	""")

	stream.write("""
  subgraph cluster_01 { 
    key [shape=none, label=<<table border="0" cellpadding="" cellspacing="0" cellborder="1">
      <tr><td colspan="2">""" + page_title + """</td></tr>
 	""")

	# Prints the documentation of the main module, if any.
	try:
		# Maybe the documentation of the script.
		stream.write('<tr><td colspan="2">' + StrWithBr( sys.modules['__main__'].__doc__ ) + '</td></tr>')
	except Exception:
		pass

	# BEWARE: Port numbers syntax ":8080/" is forbidden in URIs: Strange bug !
	stream.write('<tr><td colspan="2" href="' + topUrl + '">' + DotUL("Top") + '</td></tr>')

	stream.write("""
      <tr><td colspan="2">""" + time.strftime("%Y-%m-%d %H:%M:%S") + """</td></tr>
      <tr><td>Nodes</td><td>""" + str(len(grph)) + """</td></tr>
 	""")

	# So we can change parameters of this CGI script.
	urlEdit = ModedUrl("edit")
	urlHtml = ModedUrl("html")
	urlRdf = ModedUrl("rdf")

	urlEditReplaced = UrlToSvg( urlEdit )
	urlHtmlReplaced = UrlToSvg( urlHtml )
	urlRdfReplaced = UrlToSvg( urlRdf )

	# BEWARE: Port numbers syntax ":8080/" is forbidden in URIs: Strange bug !
	# SO THESE LINKS DO NOT WORK ?????
	stream.write("<tr><td colspan='2' href='" + urlHtmlReplaced + "'>" + DotUL("As HTML") + "</td></tr>")
	stream.write("<tr><td colspan='2' href='" + urlRdfReplaced + "'>" + DotUL("As RDF") + "</td></tr>")

	if len( parameters ) > 0 :
		stream.write("<tr><td colspan='2' href='" + urlEditReplaced + "'>" + DotUL( "Parameters edition" ) + "</td></tr>" )

	arguments = cgi.FieldStorage()
	for keyParam,valParam in parameters.items():
		try:
			actualParam = arguments[keyParam].value
		except KeyError:
			actualParam = valParam
		stream.write('<tr><td>%s</td><td>%s</td></tr>' % ( keyParam, actualParam ) )

	if errMsg != None:
		stream.write('<tr><td align="right" colspan="2">%s</td></tr>' % errMsg)

	if isSubServer:
		urlStop = ModedUrl("stop")
		urlStopReplaced = UrlToSvg( urlStop )
		stream.write('<tr><td colspan="2" href="' + urlStopReplaced + '">' + DotUL("Stop subserver") + '</td></tr>' )
		# TODO: Add an URL for subservers management, instead of simply "stop"
		# Maybe "mode=ctrl".This will list the feeders with their entity_id.
		# So they can be selectively stopped.

	stream.write("""
      </table>>]
  }
 	""")

# Returns a string for an URL different from "entity.py" etc...
# TODO: Ca serait mieux de passer le texte avec la property.
def ExternalToTitle(extUrl):
	if re.match( ".*/yawn/.*", extUrl ):
		return "Yawn"

	if re.match( ".*/objtypes_wbem.py.*", extUrl ):
		return "Subtypes"

	if re.match( ".*/file_directory.py.*", extUrl ):
		return "Subdir"

	if re.match( ".*/file_to_mime.py.*", extUrl ):
		return "MIME"
		# "C:\Users\rchateau\Developpement\ReverseEngineeringApps\PythonStyle\Icons.16x16\fileicons.chromefans.org\divx.png"
		# This cannot work this way.
		# return '<IMG SRC="Icons.16x16/fileicons.chromefans.org/divx.png" />'

	if re.match( ".*/dir_to_html.py.*", extUrl ):
		return "DIR"

	return "CGIPROP"


# Used for transforming into SVG format.
def Rdf2Dot( grph, logfil, stream, PropsAsLists ):
	fieldsSet = collections.defaultdict(list)
	nodes = {}

	def node(x):
		try:
			return nodes[x]
		except KeyError:
			nodelabel = "nd_%d" % len(nodes)
			nodes[x] = nodelabel
			return nodelabel

	# Edge label.
	# Transforms "http://primhillcomputers.com/ontologies/ppid" into "ppid"
	# TODO: Beware, a CGI parameter might be there. CGIPROP
	def qname(x, grph):
		try:
			q = grph.compute_qname(x)
			# q[0] is the shortened namespace "ns"
			# Could return q[0] + ":" + q[2]
			return q[2]
		except:
			return x

		return lib_properties.prop_color(prop)

	# Display in the DOT node the list of its literal properties.
	def FieldsToHtmlVertical(grph, the_fields):
		props = {} 
		idx = 0
		# TODO: The sort must put at first, some specific keys.
		for ( key, val ) in sorted(the_fields):
			# This should come first.
			if key == pc.property_information:
				# Completely left-aligned.
				val = StrWithBr(val)
				currTd = "<td align='left' balign='left' colspan='2'>%s</td>" % val
			elif key in [ pc.property_html_data, pc.property_rdf_data_nolist ] :
				urlTxt = lib_naming.ParseEntityUri(val)[0]
				splitTxt = StrWithBr(urlTxt)
				currTd = '<td href="%s" align="left" colspan="2">%s</td>' % ( val, splitTxt )
			else:
				val = StrWithBr(val)
				key_qname = qname( key, grph )
				currTd = "<td align='left' valign='top'>%s</td><td align='left' balign='left'>%s</td>" % ( DotBold(key_qname), val )

			props[idx] = currTd
			idx += 1
		return props

	# Ca liste les labels des objects qui apparaissent dans les blocs,
	# et pointent vers le nom du record.
	# TODO: Quand on sera bien rode, on pourra peut-etre fusionner avec node_as_lists[]
	ListedLeavesToRootLabels = {}

	listed_props_by_subj = collections.defaultdict(list)

	# TODO: Une premiere passe pour batir l'arbre d'une certaine propriete.
	# Si pas un DAG, tant pis, ca fera un lien en plus.
	# ON voulait batir des records, mais les nodes dans un record ne peuvent pas
	# avoir un URL: Donc ca va pas evidemment.
	# HTML-LIKE Labels avec PORT et PORTPOS.
	# CA VA AUSSI SIMPLIFIER L'AFFICHAGE DES TRUCS ENORMES: Modules, Fichiers etc...
	# Et on pourra trier car il y a un ordre.
	# Donc ca doit etre facile d'ajouter des proprietes affichees comme ca.

	# Exhaustive list of columns of the descendants of each subject.
	# unique_props_by_subj = collections.defaultdict(set)

	logfil.write( TimeStamp()+" Rdf2Dot: First pass\n" )
	logfil.flush()

	for subj, prop, obj in grph:

		if prop in PropsAsLists:
			listed_props_by_subj[ subj ].append( obj )

			# Maybe we already entered it: Not a problem.
			namObj = node(obj)
			# The node in which we are.
			ListedLeavesToRootLabels[ namObj ] = node(subj)

			continue

		subjNam = node(subj)

		#prop pourra etre un dictionnaire, mais ca n est pas standard:
		#prop = {"title":"lkjlkj","bidirect": True}
		# Ou alors un UriRef mais avec des parametres CGI: "http://primhillcomputers.com/ontologies/socket_end?dir=bi&title=Socket"
		# "http://primhillcomputers.com/ontologies/html_data?title=Yawn"
		# On va splitter "prop" et on le recree sans ses parametres CGI.
		# TODO: CGIPROP

		if isinstance(obj, (rdflib.URIRef, rdflib.BNode)):

			# TODO: CGIPROP. On extrait le script, uniquement.
			# Ou bien on extrait une propriete du style "is_html" ou "is_rdf_script".
			# "is_rdf_scritp", ce n est pas une autre entity.py, c'est un autre script.
			# TODO: MAIS ALORS, POURQUOI NE PAS PARSER LE SCRIPT ????
			# TODO: SI CA CONTIENT entity.py, C EST UNE REFERENCE,
			# TODO: SINON C EST DU SUB-RDF.
			# POUR LES NOMMER, ON PEUT HARD-CODER, CAR Y EN A PAS BEAUCOUP.

			prp_col = lib_properties.prop_color(prop)

			# TODO: All commutative relation have bidirectional arrows.
			# We filter with the property so it is much faster.
			# At the moment, only one property can be bidirectional.
			# TODO: CGIPROP. On extrait la propriete "edge_style" ??
			# TODO: Mais la c est different car on fusionne deux aretes ....
			if prop == pc.property_socket_end:
				objNam = node(obj)
				if ( obj, prop, subj ) in grph :
					if subjNam < objNam:
						stream.write(pattEdgeBiDir % (subjNam, objNam, prp_col, qname(prop, grph)))
				else:
					# One connection only: We cannot see the other.
					stream.write(pattEdgeOrien % (subjNam, objNam, prp_col, qname(prop, grph)))
			elif prop in [ pc.property_html_data , pc.property_rdf_data_nolist, pc.property_image ]:
				# TODO: Il suffit de tester si obj est un url de la forme "entity.py" ???
				# HTML and images urls can be "flattened" because the nodes have no descendants.
				# Do not create a node for this.
				# TODO: CGIPROP: Peut-on avoir plusieurs html ou sub-rdf ?? Il faut !
				fieldsSet[subj].append( ( prop, obj ) )
			else:
				objNam = node(obj)
				# C est la que si subjNam est dans une liste de listed_props_by_subj,
				# il faut rajouter devant, le nom du record, c est a dire SON subjNam + "_table_rdf_data:".
				if subjNam in ListedLeavesToRootLabels:
					# Syntax with colon required by DOT.
					subjNam = "rec_" + ListedLeavesToRootLabels[ subjNam ] + ":" + subjNam

				stream.write(pattEdgeOrien % (subjNam, objNam, prp_col, qname(prop, grph)))
		elif obj == None:
			# No element created in nodes[]
			fieldsSet[subj].append((prop, "Null" ))
		else:
			# For Literals. No element created in nodes[]
			# Literals can be processed according to their type.
			# Some specific properties cannot have children so they can be stored as literals?
			# Les proprietes comme "pid", on devrait plutot afficher le lien vers le process, dans la table ???
			# Les URLs de certaines proprietes sont affichees en colonnes.
			# Ou bien pour ces proprietes, on recree un entity.py ??
			fieldsSet[subj].append( ( prop, cgi.escape(obj) ) )

	logfil.write( TimeStamp()+" Rdf2Dot: Replacing vectors: PropsAsLists=%d.\n" % ( len( PropsAsLists ) ) )
	logfil.flush()

	# Maintenant, on remplace chaque vecteur par un seul gros objet, contenant une table HTML.
	if len( PropsAsLists ) > 0:
		logfil.write( TimeStamp()+" Rdf2Dot: listed_props_by_subj=%d.\n" % ( len( listed_props_by_subj ) ) )
		logfil.flush()

		# TODO: Avoid creation of temporary list. "for k, v in six.iteritems(d):"
		for subj, nodLst in list( listed_props_by_subj.items() ):
			subjNam = node(subj)

			subjNamTab = "rec_" + subjNam
			if subjNam in ListedLeavesToRootLabels:
				subjNam = "rec_" + ListedLeavesToRootLabels[ subjNam ] + ":" + subjNam

			stream.write(pattEdgeOrien % (subjNam, subjNamTab, "GREEN", "RDF data"))

			( labText, entity_graphic_class, entity_id) = lib_naming.ParseEntityUri( subj )


			# Probleme avec les champs:
			# Faire une premiere passe et reperer les fields, detecter les noms des colonnes, leur attribuer ordre et indice.
			# Seconde passe pour batir les lignes.
			# Donc on ordonne toutes les colonnes.
			# Pour chaque field: les prendre dans le sens du header et quand il y a un trou, colonne vide.
			# Inutile de trier les field, mais il d'abord avoir une liste complete des champs, dans le bon sens.
			# CA SUPPOSE QUE DANS FIELDSSET LES KEYS SONT UNIQUES.
			# SI ON NE PEUT PAS, ALORS ON METTRA DES LISTES. MAIS CETTE CONTRAINTE SIMPLIFIE L'AFFICHAGE.

			# DOMMAGE QU ON SCANNE LES OBJETS DEUX FOIS UNIQUEMENT POUR AVOIR LES NOMS DES CHAMPS !!!!!!!!!!!!!
			# TODO: HEURISTIQUE: ON pourrait s'arreter aux dix premiers. Ou bien faire le tri avant ?
			# On bien prendre les colonnes de la premiere ligne, et recommencer si ca ne marche pas.
			# Unique columns of the descendant of this subject.
			rawFieldsKeys = set()
			for obj in nodLst:
				# One table per node.
				for fld in fieldsSet[obj]:
					rawFieldsKeys.add( fld[0] )

			# sys.stderr.write("rawFieldsKeys BEFORE =%s\n" % str(rawFieldsKeys) )

			# Mandatory properties must come at the beginning of the columns of the header, with first indices.
			# BUG: Si on retire html de cette liste alors qu il y a des valeurs, colonnes absente.
			# S il y a du html ou du RDF, on veut que ca vienne en premier.
			fieldsKeysOrdered = [ "UNUSED_PLACEHOLDER_FOR_INFORMATION"]
			for fldPriority in [ pc.property_html_data, pc.property_rdf_data_nolist ]:
				try:
					# Must always be appended. BUT IF THERE IS NO html_data, IS IT WORTH ?
					# TODO: Remove if not HTML and no sub-rdf. CGIPROP

					# If the property is never used, exception then next property.
					rawFieldsKeys.remove( fldPriority )
					fieldsKeysOrdered.append( fldPriority )
				except KeyError:
					pass

			# This one is always removed because its content is concatenated at the first column.
			for fldToRemove in [ pc.property_information ]:
				try:
					rawFieldsKeys.remove( fldToRemove )
				except KeyError:
					pass

			# TODO: Remove columns when the corresponding property (For example "html",
			# "sub-rdf", "image" never has a value.
			# OU/ET ALORS: Ne pas les afficher quand ca n'a pas de sens comme par exemple les scripts.

			# Appends rest of properties, sorted.
			fieldsKeys = fieldsKeysOrdered + sorted(rawFieldsKeys)

			# sys.stderr.write("fieldsKeys=%s\n" % str(fieldsKeys) )

			# This assumes that the header columns are sorted.
			#keyIndices = dict()
			#numKeys = 0
			#for key in fieldsKeys:
			#	keyIndices[key] = numKeys
			#	numKeys += 1
			keyIndices = { key:numKeys for (numKeys,key) in enumerate(fieldsKeys,0) }

			# Apparently, no embedded tables.
			dictLines = dict()
			for obj in nodLst:
				# One table per node.
				subObjId = node(obj)

				# Beware "\L" which should not be replaced by "<TABLE>" but this is not the right place.
				subNodUri = obj.replace('&','&amp;')

				try:
					(subObjNam, subEntityGraphicClass, subEntityId) = lib_naming.ParseEntityUri( obj )
				except UnicodeEncodeError:
					sys.stderr.write( "UnicodeEncodeError error:%s\n" % ( obj ) )
					(subObjNam, subEntityGraphicClass, subEntityId) = ("Utf problem1","Utf problem2","Utf problem3")
		
				# Attention, on ne peut pas utiliser <b> avec les anciennes versions.
				numKeys = len(keyIndices)

				# TODO: HOW AND WHEN CAN IT HAPPEN ???
				if numKeys == 0:
					numKeys=1

				# Some columns might not have a value.
				columns = ["<td></td>"] * numKeys

				# Just used for the vertical order of lines, one line per object.
				title = ""
				# TODO: CGIPROP. This is not a dict, the same key can appear several times ?
				for ( key, val ) in fieldsSet[obj]:

					if key == pc.property_information:
						# This can be a short string only.
						title += val
						continue

					idxKey = keyIndices[key]

					if key in [ pc.property_html_data, pc.property_rdf_data_nolist ] :
						# TODO: get the text with ParseEntityUri if property_rdf_data_nolist
						# Ou alors: Eviter d afficher toujours le meme texte ou bien repeter l autre lien.
						# Il faut plutot afficher quelque chose de specifique, par exemple
						# l'extension de fichier si file_to_mime.py ?
						# C est utilise dans trois cas:
						# HTML:
						#   - Afficher le contenu du fichier en tant que type MIME. On aimerait une icone.
						#   - Ou bien le type de lien, par exemple "Yawn"
						# SUB-RDF:
						#   - Afficher le sous-directory.
						#   - Afficher les sous-classes si classe WBEM ou WMI.
						# Ou bien passer l info, qui doit etre courte, avec la chaine ?
						#
						# TODO: CGIPROP
						# Les liens externes peuvent etre affiches de plusieurs facons:
						# - Une colonne par titre de lien: "YAWN", "Sub-dir", "sub-classes","MIME" ...
						#   Oui mais que met-on pour visualiser le lien dans la celleue ? On repete ?
						# - Une seule colonne, et on concatene les liens externes: Ca prend moins de place.
						# => DONC, A FAIRE:
						# - On se garde la possibilite d avoir plusieurs colonnes avec traitement special.
						# - On extrait de l'url le texte du lien, de facon predefinie, ce qui est possible
						#   car c est nous qui les ajoutons.
						# - Un objet peut avoir plusieurs pc.property_html_data, pc.property_rdf_data_nolist

						valTitle = ExternalToTitle(val)
						# We insert a table because there might be several links.
						# columns[ idxKey ] = '<td href="%s" align="left" >CGIPROP...</td>' % val
						# We insert a table because there might be several links.
						# TODO: NOT FOR THE MOMENT SO IT IS NOT USEFUL.
						columns[ idxKey ] = '<td><table border="0"><tr><td href="%s" align="left" >%s</td></tr></table></td>' % ( val , valTitle )

					elif key == pc.property_image:
						# TODO: Should do something with images.
						columns[ idxKey ] = '<td><img src="%s"  scale="true" /></td>' % val
					elif val.isnumeric(): 
						columns[ idxKey ] = "<td align='right'>%s</td>" % val
					else:
						# Wraps the string if too long. Can happen only with a literal.
						columns[ idxKey ] = "<td align='left'>%s</td>" % StrWithBr(val)


				# The title has colspan=2, and the table two columns.
				if title == "":
					columns[0] = '<td port="%s" href="%s" colspan="2" align="LEFT" >%s</td>' \
						% ( subObjId, subNodUri, subObjNam )
					title_key = subObjNam
				else:
					columns[0] = '<td port="%s" href="%s" align="LEFT" >%s</td><td align="LEFT" >%s</td>' \
						% ( subObjId, subNodUri, title, subObjNam )
					title_key = title

				# Several scripts might have the same help text, so add a number.
				# "Title" => "Title"
				# "Title" => "Title/2"
				# "Title" => "Title/3" etc...
				# Beware that it is quadratic with the number of scripts with identical info.
				title_idx = 2
				title_uniq = title_key
				while title_uniq in dictLines:
					title_uniq = "%s/%d" % ( title_key, title_idx )
					title_idx += 1

				# TODO: L'ordre est base sur les chaines mais devrait etre base sur
				# TODO: ... contenu. Exemple:
				# "(TUT_UnixProcess) Handle=10" vient avant "(TUT_UnixProcess) Handle=2"
				# title_uniq devrait etre plutot la liste des proprietes.
				dictLines[ title_uniq ] = "".join( columns )

			# Replace the first column by more useful information.
			header = "<td colspan='2' border='1'>" + DotBold("%d element(s)" % len(nodLst) ) + "</td>"
			for key in fieldsKeys[1:]:
				header += "<td border='1'>" + DotBold( qname(key,grph) ) + "</td>"
			# With an empty key, it comes first after sorting.
			dictLines[""] = header

			# MAYBE SHOULD BE DONE TWICE !!!!! SEE ALSO ELSEWHERE !!!!
			labB = subj.replace('&','&amp;')

			# ATTENTION: La forme du record est celle du sujet.
			# ca veut donc dire qu'on va avoir la meme couleur pour des objets de types
			# differents s'ils sont dans la meme relation avec un sujet identique ?
			# TODO: Apparently "BLUE" is not used !
			numFields = len(fieldsKeys) + 1

			# ATTENTION: entity_graphic_class doit etre du type des URI contenus dans la table, pas le contenant !!
			try:
				# This arbitrarily take the last class. Maybe use it to change the style of each line.
				# Also, if these are subclasses of files, we could use a "folder" as shape.
				# Priority for the title.
				table_graphic_class = entity_graphic_class
			except Exception:
				# If this is not defined, take the last processed row.
				table_graphic_class = subEntityGraphicClass

			# TODO: Le titre est le contenu ne sont pas forcement de la meme classe.
			labTextWithBr= StrWithBr( labText )
			lib_patterns.WritePatterned( stream, table_graphic_class, subjNamTab, "help text", "BLUE", labB, numFields, labTextWithBr, dictLines )

			# TODO: Eviter les repetitions de la meme valeur dans une colonne en comparant d une ligne a l autre.
			# TODO: Si une cellule est identique jusqu a un delimiteur, idem, remplacer par '"'.


	logfil.write( TimeStamp()+" Rdf2Dot: Display remaining nodes. nodes=%d\n" % len(nodes) )
	logfil.flush()

	# Maintenant on affiche les noeuds qui restent.
	# TODO: Avoid converting to a list.
	for obj, nam in list(nodes.items()):
		# x contains something like: ns1:pid "3280"^^xsd:integer
		# So this eliminates the namespace and the value type.
		# TODO: This should removes the double-quotes surrounding the value.

		if nam in ListedLeavesToRootLabels :
			continue

		props = FieldsToHtmlVertical( grph, fieldsSet[obj])

		#IMPOSSIBLE DE METTRE UN AMPERSAND DANS LE HTML DU FICHIER "dot"
		# Sauf avec une vieille version de dot, sous Unix.
		# C'est pourquoi nos URLs n'ont qu'un seul argument, le xid, type et id.
		# dot - Graphviz version 2.20.3 (Sat Jan 17 00:45:25 UTC 2009)
		# Mais par ailleurs elle core dump, parfois.
		# TODO: PEUT-ETRE SUFFIT-IL DE DOUBLER L'AMPERSAND ?!?!?!?  MAYBE DOUBLE amp;amp; ???
		# TODO: Apparemment ca marche: Les ampersand dans le HTML des fichiers DOT doivent etre doubles:
		# nd_1 [ shape=none, tooltip="root/CIMV2/" color=black label=< <table color='#666666' cellborder='0'
		#   cellspacing='0' border='1'><tr>
		#   <td href='http://127.0.0.1:80/Survol/htbin/objtypes_wmi.py?xid=root/CIMV2/:&amp;amp;cimom=127.0.0.1' bgcolor='#99BB88' colspan='2'>root/CIMV2/  cimom=127.0.0.1</td></tr></table> > ]
		labHRef = obj.replace('&','&amp;')

		try:
			# TODO: Probleme ici: La chaine est deja codee pour HTML ce qui en rend le parsing different
			# TODO: ... de celui d'un URL deja decode. DOMMAGE: On quote puis unquote !!!
			# (labText, entity_graphic_class, entity_id) = lib_naming.ParseEntityUri( obj )
			(labText, entity_graphic_class, entity_id) = lib_naming.ParseEntityUri( unquote(obj) )
		except UnicodeEncodeError:
			sys.stderr.write( "UnicodeEncodeError error:%s\n" % ( obj ) )

		# WritePatterned va recevoir un tableau de chaines de la forme "<td>jhh</td><td>jhh</td><td>jhh</td>"
		# et c est lui qui va mettre des <tr> et </tr> de part et d'autre.
		# Ca evite des concatenations. Dans le cas de "Vertical", on va donc renvoyer un tableau"

		# Les ampersand sont doubles intentionnelent car ils ensuite remplaces deux fois.
		# Ca n'est utilise que temporairement le temps qu'on remplace les arguments CGI par de vrais Monikers WMI.
		labTextClean = StrWithBr( labText.replace("&amp;amp;"," "))
		lib_patterns.WritePatterned( stream, entity_graphic_class, nam, entity_graphic_class, NODECOLOR, labHRef, 2, labTextClean, props )

	logfil.write( TimeStamp()+" Rdf2Dot: Leaving\n" )
	logfil.flush()
	stream.write("}\n")

################################################################################
def CopyToOutPy3(logfil,svg_out_filnam,out_dest):
	logfil.write( TimeStamp() + " Output with conversion:%s\n" % svg_out_filnam )
	logfil.flush()
	# Windows Python 3.
	# TODO: AVOID THIS EXPENSIVE CONVERSION !!
	infil = open(svg_out_filnam,'r',encoding='UTF-8')

	filSz = os.path.getsize(svg_out_filnam)
	logfil.write( TimeStamp() + " End of open. filSz=%d\n" % filSz )
	logfil.flush()
	content = infil.read()
	nbOut = out_dest.write( bytes( content, 'UTF-8') )
	infil.close()
	logfil.write( TimeStamp() + " End of output with conversion: %d chars\n" %nbOut )

def CopyToOutPyExperimental(logfil,svg_out_filnam,out_dest):
	time.sleep(10.0)

	logfil.write( TimeStamp() + " Output without conversion EXPERIMENTAL: %s\n" % svg_out_filnam  )
	logfil.flush()
	# Linux or Windows Python2.
	infil = open(svg_out_filnam,'r')

	filSz = os.path.getsize(svg_out_filnam)
	logfil.write( TimeStamp() + " End of codecs open. filSz=%d\n" % filSz )
	logfil.flush()

	# No idea why but it blocks reading 500kbytes.
	logfil.write( TimeStamp() + " After flush. Reading\n" )
	strInRead = infil.read()
	logfil.write( TimeStamp() + " End of infil read:%d\n" % len(strInRead) )
	nbOut = out_dest.write( strInRead )
	logfil.write( TimeStamp() + " End of output without conversion: %s chars\n" % str(nbOut) )

	infil.close()

def CopyToOutPy2(logfil,svg_out_filnam,out_dest):
	logfil.write( TimeStamp() + " Output without conversion: %s\n" % svg_out_filnam  )
	logfil.flush()
	# Linux or Windows Python2.
	import codecs
	infil = codecs.open(svg_out_filnam,'r',encoding='utf8')
	filSz = os.path.getsize(svg_out_filnam)
	logfil.write( TimeStamp() + " End of codecs open. filSz=%d\n" % filSz )
	logfil.flush()

	# No idea why but it blocks reading 500kbytes.
	logfil.write( TimeStamp() + " After flush. Reading\n" )
	strInRead = infil.read()
	logfil.write( TimeStamp() + " End of infil read:%d\n" % len(strInRead) )
	nbOut = out_dest.write( strInRead )
	logfil.write( TimeStamp() + " End of output without conversion: %s chars\n" % str(nbOut) )

	infil.close()

def CopyToOut(logfil,svg_out_filnam,out_dest):
	if sys.version_info >= (3,):
		CopyToOutPy3(logfil,svg_out_filnam,out_dest)
	else:
		# CopyToOutPyExperimental(logfil,svg_out_filnam,out_dest)
		# CopyToOutPy3(logfil,svg_out_filnam,out_dest)
		# Ca bloque sur des gros fichiers avec Python2 et Windows7.
		CopyToOutPy2(logfil,svg_out_filnam,out_dest)
	logfil.flush()

################################################################################

# TODO: Est-ce vraiment necessaire ?????????????
# Peut-etre oui, a cause des sockets ?
def WrtAsUtf(out,str):
	out.write( str.encode('utf-8') )

# Default destination for the RDF, HTML or SVG output.
def DfltOutDest(out_dest=None):
	if out_dest == None:
		if sys.version_info >= (3,):
			return sys.stdout.buffer
		else:
			return sys.stdout
	else:
		return out_dest

# TODO: Consider using pygraphviz: Small speedup probably.
# But the priority is to chase graphes which are too long to route.
# TODO: Problem: The resulting graph is not deterministic.
# Should compare the generated DOT files to see of they are identical.
def Dot2Svg(dot_filnam_after,logfil, viztype, out_dest = None, removeHeader = False):
	sys.stderr.write("viztype=%s\n"%(viztype) )
	out_dest = DfltOutDest(out_dest)
	tmpSvgFil = TmpFile("Dot2Svg","svg")
	svg_out_filnam = tmpSvgFil.Name
	# dot -Kneato

	# Dot/Graphviz no longer changes PATH at installation. It must be done BEFORE.
	if lib_util.isPlatformWindows:
		dot_path = 'dot.exe'
	else:
		dot_path = "dot"

	if lib_util.isPlatformLinux:
		# TODO: This is arbitrary because old Graphviz version.
		dotFonts = ["-Gfontpath=/usr/share/fonts/TTF", "-Gfontnames=svg", "-Nfontname=VeraBd.ttf","-Efontname=VeraBd.ttf"]
	else:
		dotFonts = []

	# Old versions of dot need the layout on the command line.

	dotClassical = False
	if dotClassical:
		svg_command = dot_path + " -K" + viztype + " -Tsvg " + dot_filnam_after + " -o " + svg_out_filnam \
			+ ' '.join(dotFonts) + " -v  -Goverlap=false 2>&1"

		logfil.write( "Dot command:%s\n" % svg_command )
		# http://www.graphviz.org/doc/info/attrs.html#d:fontname
		svg_stream = os.popen(svg_command)

		logfil.write( TimeStamp()+" Dot command output:\n" )
		for svg_line in svg_stream:
			logfil.write( svg_line )
		logfil.write( "\n" )
	else:
		# This is maybe a bit faster than os.open because no shell and direct write to the output.
		# This works with Python 3.2 on Windows.
		import subprocess
		svg_command = [ dot_path,"-K",viztype,"-Tsvg",dot_filnam_after,"-o",svg_out_filnam, \
			"-v","-Goverlap=false" ] + dotFonts
		msg = "svg_command=" + " ".join(svg_command) + "\n"
		sys.stderr.write(msg)
		logfil.write(TimeStamp()+" "+msg)

		ret = subprocess.call( svg_command, stdout=logfil, stderr=logfil, shell=False )
		logfil.write(TimeStamp()+" Process ret=%d\n" % ret)

	if not os.path.isfile( svg_out_filnam ):
		ErrorMessageHtml("SVG file " + svg_out_filnam + " could not be created." )
	
	# If there is an error, we should write it as an HTML page.
	# On the other hand it will be impossible to pipe the output
	# because it would assume a SVG document.
	# TODO: See that later.

	# For the specific case when it writes into a socket. Strange behaviour:
	# Without this, it wraps our SVG code in HTML tags, adds its own HTTP header, etc...
	# The test on stdout comes at the end because it does not work on old Python versions.
	if lib_util.isPlatformWindows and sys.version_info >= (3,4,) and out_dest != sys.stdout.buffer :
		logfil.write( TimeStamp() + " SVG Header removed\n" )
		logfil.flush()
	else:
		logfil.write( TimeStamp() + " Writing SVG header\n" )
		logfil.flush()
		lib_util.HttpHeader( out_dest, "image/svg+xml" )

	# Here, we are sure that the output file is closed.
	CopyToOut(logfil,svg_out_filnam,out_dest)

################################################################################

def Grph2Svg( page_title, topUrl, error_msg, isSubServer, parameters, dot_style, grph, out_dest ):
	tmpLogFil = TmpFile("Grph2Svg","log")
	logfil = open(tmpLogFil.Name,"w")
	logfil.write( "Starting logging\n" )

	tmpDotFil = TmpFile("Grph2Dot","dot")
	dot_filnam_after = tmpDotFil.Name
	rdfoutfil = open( dot_filnam_after, "w" )
	logfil.write( TimeStamp()+" Created "+dot_filnam_after+"\n" )
	logfil.flush()

	dot_layout = WriteDotHeader( page_title, dot_style['layout_style'], rdfoutfil, grph )
	WriteDotLegend( page_title, topUrl, error_msg, isSubServer, parameters, rdfoutfil, grph )
	logfil.write( TimeStamp()+" Legend written\n" )
	logfil.flush()
	Rdf2Dot( grph, logfil, rdfoutfil, dot_style['collapsed_properties'] )
	logfil.write( TimeStamp()+" About to close dot file\n" )
	logfil.flush()

	# Do this because the file is about to be reopened from another process.
	rdfoutfil.flush()
	os.fsync( rdfoutfil.fileno() )
	rdfoutfil.close()

	# TODO: No need to tell it twice because it is superseded in the dot file.
	# TEMP TEMP ONLY WINDOWS AND PYTHON 34
	removeHeader = isSubServer
	Dot2Svg( dot_filnam_after, logfil, dot_layout, out_dest, removeHeader )
	logfil.write( TimeStamp()+" closing log file\n" )
	logfil.close()

################################################################################

# Transforms a RDF graph into a HTML page.
def Grph2Html( page_title, error_msg, isSubServer, parameters, grph, out_dest = None):
	out_dest = DfltOutDest(out_dest)
	# TODO: Est-ce necessaire d'utiliser WrtAsUtf au lieu de print() ?
	# Peut-etre oui, a cause des sockets?
	WrtAsUtf( out_dest, "Content-type: text/html\n\n<head>" )

	# TODO: Encode the HTML special characters.
	WrtAsUtf( out_dest, "<title>" + page_title + "</title>")

	# TODO: Essayer de rassembler les literaux relatifs au memes noeuds, pour faire une belle presentation.

	WrtAsUtf( out_dest, ' </head> <body>')

	WrtAsUtf( out_dest,'<table border="1">')

	WrtAsUtf( out_dest,'<tr><td colspan="3"><a href="' + ModedUrl("edit") + '">CGI parameters edition</a></td></tr>')

	for keyParam,valParam in parameters.items():
		WrtAsUtf( out_dest,'<tr><td>' + keyParam + '</td><td colspan="2">' + valParam + '</td></tr>')

	WrtAsUtf( out_dest,'<tr><td colspan="3"><a href="' + ModedUrl("svg") + '">Content as SVG</a></td></tr>')
	WrtAsUtf( out_dest,'<tr><td colspan="3"><a href="' + ModedUrl("rdf") + '">Content as RDF</a></td></tr>')
	WrtAsUtf( out_dest,'<tr><td colspan="3">' + str(len(grph)) + ' nodes</td></tr>')

	if error_msg != None:
		WrtAsUtf( out_dest,'<tr><td colspan="3"><b>' + error_msg + '</b></td></tr>')

	if isSubServer:
		WrtAsUtf( out_dest,'<tr><td colspan="3"><a href="' + ModedUrl("stop") + '">Stop subserver</a></td></tr>')

	by_subj = dict()
	for subj, pred, obj in grph:
		# No point displaying some keys if there is no value.
		if pred in [ pc.property_image, pc.property_information ] :
			if str(obj) == "":
				continue

		the_tup = ( pred, obj )
		try:
			by_subj[ subj ].append( the_tup )
		except KeyError:
			by_subj[ subj ] = [ the_tup ]

	for subj, the_tup_list in list( by_subj.items() ):

		subj_str = str(subj)
		subj_title = lib_naming.ParseEntityUri(subj_str)[0]

		cnt_rows = len( the_tup_list )

		mustWriteColOne = True

		for pred, obj in the_tup_list:
			WrtAsUtf( out_dest, "<tr>" )

			if mustWriteColOne:
				WrtAsUtf( out_dest, '<td rowspan="' + str(cnt_rows) + '"><a href="' + subj_str + '">'+ subj_title +"</a></td>")
				mustWriteColOne = False

			obj_str = str(obj)

			if isinstance( obj , (rdflib.URIRef, rdflib.BNode)):
				obj_title = lib_naming.ParseEntityUri(obj_str)[0]
				if pred == pc.property_image :
					WrtAsUtf( out_dest, "<td colspan='2'><img src='" + obj_str + "' alt='Alt image' title='Titre image'></td>")
				else:
					WrtAsUtf( out_dest, "<td>" + AntiPredicateUri(str(pred)) + "</td>")
					url_with_mode = ConcatenateCgi( obj_str, "mode=html" )
					WrtAsUtf( out_dest, '<td><a href="' + url_with_mode + '">' + obj_title + "</a></td>")
			else:
				if pred == pc.property_information :
					WrtAsUtf( out_dest, '<td colspan="2">' + obj_str + "</td>")
				else:
					WrtAsUtf( out_dest, '<td>' + AntiPredicateUri(str(pred)) + "</td>")
					WrtAsUtf( out_dest, '<td>' + obj_str + "</td>")

			WrtAsUtf( out_dest, "</tr>")

	WrtAsUtf( out_dest, " </table> </body> </html> ")


################################################################################

# Used by all CGI scripts when they have finished adding triples to the current RDF graph.
# This just writes a RDF document which can be used as-is by browser,
# or by another scripts which will process this RDF as input, for example when merging RDF data.
# Consider adding reformatting when the output is a browser ... if this can be detected !!
# It is probably possible with the CGI environment variable HTTP_USER_AGENT.
# Also, the display preference could be stored with the Python library cookielib.
#
# AUSSI: On pourrait, sous certaines conditions, transformer la sortie en HTML ou en SVG
# (Et/ou envoyer du Javascript avec des appels rdfquery pour affichage dans le navigateur)
# Ca pourrait dependre d'une variable CGI: mode=RDF/HTML etc...
# Ici: On peut prendre la valeur de "mode" en dissequant l'URL du Referer.
# Petit probleme toutefois avec Graphviz/Dot sous Windows qui nous fait
# des soucis quand un Url contient un ampersand.
#
def Grph2Rdf(grph, out_dest):
	WrtAsUtf( out_dest, "Content-type: text/rdf\n\n")
	# Format support can be extended with plugins,
	# but 'xml', 'n3', 'nt', 'trix', 'rdfa' are built in.

	grph.serialize( destination = out_dest, format="xml")

################################################################################

# TODO: The nodes should be displayed always in the same order.
# THIS IS NOT THE CASE IN HTML AND SVG !!

def OutCgiMode( grph, topUrl, outDest, mode, pageTitle, dotLayout, errorMsg = None, isSubServer=False, parameters = dict()):
	# sys.stderr.write("OutCgiMode len=%d\n" % ( len(grph) ) )

	if mode == "html":
		Grph2Html( pageTitle, errorMsg, isSubServer, parameters, grph, outDest)
	elif mode == "rdf":
		Grph2Rdf( grph, outDest)
	else: # Or mode = "svg"
		# Default value, because cannot have several CGI arguments in a SVG document (Bug ?).
		Grph2Svg( pageTitle, topUrl, errorMsg, isSubServer, parameters, dotLayout, grph, outDest)

################################################################################

# Extracts the mode from an URL.
def GetModeFromUrl(url):
	mtch_url = re.match(".*[\?\&]mode=([a-zA-Z0-9]*).*", url)
	if mtch_url:
		return mtch_url.group(1)
	return ""

# Current URL but in edition mode.
# PROBLEM: SI PAS DE ENTITY_ID A EDITER CAR "TOP" ALORS ON REBOUCLE SUR Edit:
# DONC DETECTER LE TYPE DE L'ENTITE EN FOCNTION DU DIRECTORY ET AUCUN SI "TOP".
def ModedUrl(otherMode):
	script = lib_util.RequestUri()

	mtch_url = re.match("(.*[\?\&]mode=)([a-zA-Z0-9]*)(.*)", script)
	if mtch_url:
		edtUrl = mtch_url.group(1) + otherMode + mtch_url.group(3)
	else:
		edtUrl = ConcatenateCgi( script, "mode=" + otherMode )
	return edtUrl

# The display mode can come from the previous URL or from a CGI environment.
def GuessDisplayMode(log):
	arguments = cgi.FieldStorage()
	try:
		try:
			mode = arguments["mode"].value
		except AttributeError:
			# In case there are several mode arguments, 
			# hardcode to "info". Consequence of a nasty Javascript bug.
			mode = "info"
		if mode != "":
			log.write( "GuessDisplayMode: From arguments mode=%s\n" % (mode) )
			return mode
	except KeyError:
		pass

	try:
		# HTTP_REFERER=http://127.0.0.1/PythonStyle/print.py?mode=xyz
		referer = os.environ["HTTP_REFERER"]
		modeReferer = GetModeFromUrl( referer )
		# If we come from the edit form, we should not come back to id.
		# TODO: HOW CAN WE COME BACK TO THE FORMER DISPLAY MODE ??
		if modeReferer != "":
			if modeReferer == "edit":
				log.write("GuessDisplayMode: From edit referer %s mode=%s\n" % (referer,modeReferer) )
				# TODO: Should restore the original edit mode.
				# EditionMode
				return ""
			else:
				log.write("GuessDisplayMode: From referer %s mode=%s\n" % (referer,modeReferer) )
				return modeReferer

	except KeyError:
		pass

	try:
		# When called from another module, cgi.FieldStorage might not work.
		script = os.environ["SCRIPT_NAME"]
		mode = GetModeFromUrl( script )
		if mode != "":
			log.write("GuessDisplayMode: From script %s mode=%s\n" % (script,mode) )
			return mode
	except KeyError:
		pass

	mode = ""
	log.write("Default mode=%s\n"% (mode) )
	return mode

################################################################################

def MakeDotLayout(dot_layout, collapsed_properties ):
	return { 'layout_style': dot_layout, 'collapsed_properties':collapsed_properties }

################################################################################

# At the moment, we have: xxx.py?xid=process:4588
# We will have: xxx.py?xid=Win32_Process.Handle="123"
# ou bien, avec escape():
# xxx.py?xid=https://jdd:test@acme.com:5959/cimv2:CIM_RegisteredProfile.InstanceID="acme:1"
#
# CgiEnv.GetParameter() applies only to CGI parameter.
#
# http://www.wbemsolutions.com/tutorials/DMTF/wbem-xmlcim.html
#
# //www.acme.com/root/cimv2
# //www.acme.com/root/cimv2:CIM_RegisteredProfile
# https://jdd:test@acme.com:5959/cimv2:CIM_RegisteredProfile
# https://jdd:test@acme.com:5959/cimv2:CIM_RegisteredProfile.InstanceID="acme:1"
# 'Win32_SoftwareFeature.IdentifyingNumber="{0862D680-09AA-4B2D-8319-64C7E0BCC88D}",Name="Havana",ProductName="Havana",Version="1.0"'
# Comparaison avec WBEM Uri: On voit qu'une reference est un URI dans le meme namespace.
# CIM_IndicationSubscription.Filter=(reference)"CIM_IndicationFilter.SystemCreationClassName=(string)\"CIM_ComputerSystem\",SystemName=(string)\"server001.acme.com\",CreationClassName=(string)\"CIM_IndicationHandlerCIMXML\",Name=(string)\"Filter01\"",Handler=(reference)"CIM_IndicationHandlerCIMXML.SystemCreationClassName=(string)\"CIM_ComputerSystem\",SystemName=(string)\"server001.acme.com\",CreationClassName=(string)\"CIM_IndicationHandlerCIMXML\",Name=(string)\"Handler01\""
#
# On peut utiliser urlparse, avec
#
# >>> urlparse.urlparse( "https://jdd:test@acme.com:5959/cimv2:CIM_RegisteredProfile")
# ParseResult(scheme='https', netloc='jdd:test@acme.com:5959', path='/cimv2:CIM_RegisteredProfile')
#
# >>> urlparse.urlparse( 'Win32_SoftwareFeature.IdentifyingNumber="{0862D680-09AA-4B2D-8319-64C7E0BCC88D}",Name="Havana",ProductName="Havana",Version="1.0"')
# ParseResult(scheme='', netloc='', path='Win32_SoftwareFeature.IdentifyingNumber="{0862D680-09AA-4B2D-8319-64C7E0BCC88D}",Name="Havana",ProductName="Havana",Version="1.0"')
#
# >>> urlparse.urlparse('https://jdd:test@acme.com:5959/cimv2:CIM_RegisteredProfile.InstanceID="acme:1"')
# ParseResult(scheme='https', netloc='jdd:test@acme.com:5959', path='/cimv2:CIM_RegisteredProfile.InstanceID="acme:1"')
#
# >>> urlparse.urlparse('//127.0.0.1/cimv2:CIM_RegisteredProfile.InstanceID="acme:1"')
# ParseResult(scheme='', netloc='127.0.0.1', path='/cimv2:CIM_RegisteredProfile.InstanceID="acme:1"')
#
# Ou alors, on explose le WBEM Uri pour l'expliciter:
# xxx.py?scheme=https&netloc=jdd:test@acme.com:5959&namespace=cimv2&class=CIM_RegisteredProfile&InstanceID="acme:1"
# - On est oblige de parser nous-memes l'URI au lieu de s'en remettre a urlparse.
# - Ca n'exige pas que WMI et WBEM aient les memes uris. Ca semble etre le cas.
# - On ne peut pas utiliser l'URI aveuglement.
# - Collision avec autres variables CGI, melange de variables qui ne sont pas sur le meme plan.
#
# This parses the CGI environment variables which define an entity.
class CgiEnv():
	def __init__(self, info = "", url_icon = "", parameters = {}, can_process_remote = False, platform_regex = "" ):
		# TODO: This value is read again in OutCgiRdf, we could save time by making this object global.
		sys.stderr.write( "CgiEnv info=%s parameters=%s\n" % ( info, str(parameters) ) )
		sys.stderr.write("QUERY_STRING=%s\n" % os.environ['QUERY_STRING'] )
		mode = GuessDisplayMode(sys.stderr)

		# Contains the optional arguments, needed by calling scripts.
		self.m_parameters = parameters

		# TODO: Same here: If this CgiEnv os global, we can store 
		# the page_title which is later read by OutCgiMode.
		self.m_page_title = info

		# If we can talk to a remote host to get the desired values.
		self.m_can_process_remote = can_process_remote

		# This is used to add information to each Python script,
		# so it can be nicely displayed.
		if mode == "info":
			# TODO: Maybe add some information about the parameters ?
			# And about the arguments, but not in the "info" element,
			# because this string might be cached.
			infoDict = { "info" : info, "url_icon" : url_icon, "can_process_remote" : can_process_remote, "platform_regex" : platform_regex }
			infoDict.update( parameters )
			SerialiseScriptInfo( infoDict )
			# TODO: Cannot work with WSGI.
			sys.exit(0)

		self.m_arguments = cgi.FieldStorage()

		(self.m_entity_type,self.m_entity_id,self.m_entity_host) = self.GetXid()
		self.m_entity_id_dict = lib_util.SplitMoniker(self.m_entity_id)

		# This is probably too generous to indicate a local host.
		self.TestRemoteIfPossible(can_process_remote)

		# TODO: HOW WILL WE RESTORE THE ORIGINAL DISPLAY MODE ?
		if mode == "edit":
			self.EditionMode()

	def TestRemoteIfPossible(self,can_process_remote):
		# This is probably too generous to indicate a local host.
		if can_process_remote or self.m_entity_host is None:
			return

		# Maybe entity_host="http://192.168.1.83:5988"
		# hostOnly = lib_util.EntHostToIp(self.m_entity_host)

		if lib_util.IsLocalAddress(self.m_entity_host):
			return

		ErrorMessageHtml("Script %s cannot handle remote hosts on host=%s" % ( sys.argv[0], self.m_entity_host ) )

	# We avoid having several CGI arguments because Dot/Graphviz wants
	# no ampersand "&" in the URLs.
	def GetXid(self):
		try:
			xid = self.m_arguments["xid"].value
		except KeyError:
			# See function EditionMode
			try:
				entity_type = self.m_arguments["edimodtype"].value
				monikDelim = ""
				entity_id = ""
				for ediKey in self.m_arguments:
					if ediKey[:11] == "edimodargs_":
						monikKey = ediKey[11:]
						monikVal = self.m_arguments[ediKey].value
						entity_id += monikDelim + monikKey + "=" + monikVal
						monikDelim = "&"

				# entity_id = self.m_arguments["edimodargs_id"].value
				return ( entity_type, entity_id, "" )
			except KeyError:
				# No host, for the moment.
				return ( "", "", "" )
		return lib_util.ParseXid( xid )
	
	
	# TODO
	# Si l'argument n'est pas donne, passer en mode edition.
	# En plus, on va ajouter un menu (Dans entity ?)
	# qui permet de lister les scripts par type d'entite.
	# On rajoute le menu d'edition dans l'affichage HTML.
	# En RDF, voir si on peut ajouter un cartouche dans un coin du dessin.
	# http://stackoverflow.com/questions/3499056/making-a-legend-key-in-graphviz
	# On peut meme utiliser la meme legende ou presque.

	# A terme, on met dans un autre fichier toutes les interactions HTML,
	# car ca n'appelle pas grand chose d'autre, et est susceptible de grossir.
	# Ca sera lib_html.
	def EditionMode(self):
		# Maybe we could have that with cgi.
		formAction = os.environ['SCRIPT_NAME']

		lib_util.HttpHeader( sys.stdout, "text/html")
		print("<html>")
		print("<head></head>")
		print("<title>Editing parameters</title>")
	
		print("""
		<body>
		On utilise la methode GET pour la forme.
		ce qui permet de reutiliser l'url et d'en voir tous les arguments.
		Il y a une taille limite, mais ca nous est egal.<br>
		PROBLEME: IL FAUT REASSEMBLER ENTITY_TYPE ET ENTITY_ID, EN GENERALISANT, TOUT LE MONIKER, EN XID.
		""")
		print('<form name="myform" action="' + formAction + '" method="GET">')

		print("""
		Mettre les eventuels autres parametres de SCRIPT_NAME en parametres hidden.
		Ou bien construire dynamiquent un URL qui va etre appele en GET par javascript.
		Le CgiEnv peut aussi specifier des paremtres eidtables.
		Il faudrait aussi parser toutes les variables CGI.
		<br>TODO: NE PAS REEDITER LE MONIKER !!!
		Ce lien (mode=edit) va apparaitre dans le cartouche.<br><br>
		""")

		# Names of arguments passed as CGI parameters.
		argKeys = self.m_arguments.keys()

		print("<table>")

		if self.m_entity_type != "":
			print('<tr><td colspan=2>' + self.m_entity_type + '</td>')
			for kvKey in self.m_entity_id_dict:
				# TODO: Encode the value.
				kvVal = self.m_entity_id_dict[kvKey]
				print("<tr>")
				print('<td>' + kvKey + '</td>')
				ediNam = "edimodargs_" + kvKey
				print('<td><input type="text" name="%s" value="%s"></td>' % (ediNam,kvVal) )
				print("</tr>")

		# Now the parameters specific to the script, if they are not passed also as CGI params.
		for param_key in self.m_parameters:
		#	if not param_key in argKeys:
			print("<tr>")
			print('<td>' + param_key + '</td>')
			param_val = self.GetParameters( param_key )
			# TODO: Encode the value.
			print('<td><input type="text" name="' + param_key + '" value="' + param_val + '"><td>')
			print("</tr>")

		print("</table>")

		# Now the hidden arguments. Although entity_type can be deduced from the CGI script location.
		print('<input type="hidden" name="edimodtype" value="' + self.m_entity_type + '"><br>')

		for key in argKeys:
			# These keys are processed differently.
			if key in self.m_parameters:
				continue

			# Of course, the mode must not be "edit".
			if key == "mode":
				continue

			# ATTENTION: LES ARGUMENTS SPECIFIQUEMENT EDITABLES NE SONT PAS HIDDEN.
			# QUESTION: COMMENT EDITER UNE LISTE D'ARGUMENTS?
			# ET MEME COMMENT SAVOIR QUE C'EST UNE LISTE ?
			# IDEE: ON PASSE A CgiEnv UNE KEY QUI TERMINE PAR [].
			argList = self.m_arguments.getlist(key)
			if len(argList) == 1:
				# TODO: Values should be encoded.
				print('<input type="hidden" name="' + key + '" value="'+argList[0] + '"><br>')
			else:
				for val in argList:
					# Note the "[]" to pass several values.
					print('<input type="hidden" name="' + key + '[]" value="'+val + '"><br>')

		print('<input type="submit" value="Submit">')
		print("</form>")
		print("</body>")
		print("</html>")
		sys.exit(0)

	# These are the parameters specific to the script, which are edit in our HTML form, in EditionMode().
	# They must have a default value. Maybe we could always have an edition mode when their value
	# is not set.
	# If the parameter is "cimom", it will extract the host of Uris like these: Wee GetHost()
	# https://jdd:test@acme.com:5959/cimv2:CIM_RegisteredProfile.InstanceID="acme:1"

	def GetParameters(self,paramkey):
		try:
			# If the script parameter is passed as a CGI argument.
			# BEWARE !!! An empty argument triggers an exception !!!
			paramVal = self.m_arguments[paramkey].value
			sys.stderr.write("GetParameters %s=%s as CGI\n" % ( paramkey, paramVal ) )
		except KeyError:
			# Default value if no CGI argument.
			try:
				paramVal = self.m_parameters[paramkey]
				sys.stderr.write("GetParameters %s=%s as default\n" % ( paramkey, paramVal ) )
			except KeyError:
				lib_util.InfoMessageHtml("GetParameters no value nor default for %s\n" % paramkey )
				exit(0)

		return paramVal

	# This is used for compatibility with the legacy scripts, which has a single id.
	# Now all parameters must have a key. As a transition, GetId() will return the value of
	# the value of an unique key-value pair.
	# If this class is not in DMTF, we might need some sort of data dictionary.
	def GetId(self):
		sys.stderr.write("GetId self.m_entity_id=%s\n" % ( str( self.m_entity_id ) ) )
		try:
			# If this is a top-level url, no object type, therefore no id.
			if self.m_entity_type == "":
				return ""

			splitKV = lib_util.SplitMoniker(self.m_entity_id)
			sys.stderr.write("GetId splitKV=%s\n" % ( str( splitKV ) ) )

			# If this class is defined in our ontology, then we know
			# what is the first property.
			entOnto = lib_util.OntologyClassKeys(self.m_entity_type)
			if entOnto:
				keyFirst = entOnto[0]
				# Only if this mandatory key is in the dict.
				try:
					return splitKV[keyFirst]
				except KeyError:
					# This is a desperate case...
					pass
			# Returns the first value but this is not reliable at all.
			for key in splitKV:
				return splitKV[key]
		except KeyError:
			pass

		# If no parameters although one was requested.
		self.EditionMode()
		return ""

	# TODO: Ca va etre de facon generale le moyen d'acces aux donnees et donc inclure le cimom
	# soit par example cimom=http://192.168.1.83:5988  ou bien seulement un nom de machine.
	# C'est ce que WMI va utiliser. On peut imaginer aussi de mettre un serveur ftp ?
	# Ou bien un serveur SNMP ?
	# C est plus un serveur qu un host. Le host est plutot une propriete de l'objet,
	# pas une clef d'acces.
	# C est ce qui va permettre d acceder au meme fichier par un disque partage et par ftp.
	def GetHost(self):
		return self.m_entity_host

	# TODO: Would probably be faster by searching for the last "/".
	# '\\\\RCHATEAU-HP\\root\\cimv2:Win32_Process.Handle="0"'  => "root\\cimv2:Win32_Process"
	# https://jdd:test@acme.com:5959/cimv2:Win32_SoftwareFeature.Name="Havana",ProductName="Havana",Version="1.0"  => ""
	def GetNamespaceType(self):
		return lib_util.ParseNamespaceType( self.m_entity_type )

	def OutCgiRdf(self, grph, dot_layout = "", collapsed_properties=[] ):

		layoutParams = MakeDotLayout( dot_layout, collapsed_properties )

		out_dest = DfltOutDest()
		mode = GuessDisplayMode(sys.stderr)

		topUrl = lib_util.TopUrl( self.m_entity_type, self.m_entity_id )

		OutCgiMode( grph, topUrl, out_dest, mode, self.m_page_title, layoutParams, parameters = self.m_parameters )

################################################################################

def ErrorMessageHtml(message):
	lib_util.InfoMessageHtml(message)
	sys.exit(0)

################################################################################

def SourceDir(entity_type=""):
	if entity_type == "":
		return "/sources_top"
	else:
		return "/sources_types/" + entity_type


################################################################################

def TryDir(dir):
	if( os.path.isdir(dir) ):
		return dir
	raise Exception("Not a dir:"+dir)


def TmpDir():
	try:
		# Maybe these environment variables are undefined for Apache user.
		return TryDir( os.environ["TEMP"].replace('\\','/') )
	except Exception:
		pass

	try:
		return TryDir( os.environ["TMP"].replace('\\','/') )
	except Exception:
		pass

	if lib_util.isPlatformWindows:
		try:
			return TryDir( os.environ["TMP"].replace('\\','/') )
		except Exception:
			pass

		try:
			return TryDir( os.environ["USERPROFILE"].replace('\\','/') + "/AppData/Local/Temp" )
		except Exception:
			pass

		try:
			return TryDir( "C:/Windows/Temp" )
		except Exception:
			pass

		return TryDir( "C:/Temp" )
	else:
		return TryDir( "/tmp" )

# This will not change during a process.
tmpDir = TmpDir()
		
class TmpFile:
	def __init__(self,prefix="tmp", suffix="tmp"):
		self.Name = "%s/%s.%d.%s" % ( tmpDir, prefix, os.getpid(), suffix )
		sys.stderr.write("tmp=%s cwd=%s\n" % ( self.Name, os.getcwd() ) )

	def __del__(self):
		try:
			sys.stderr.write("Deleting="+self.Name+"\n")
			#os.remove(self.Name)
		except Exception:
			ErrorMessageHtml("Cannot delete:"+self.Name)
		return

################################################################################

# Used when displaying all files open by a process: There are many of them,
# so the useless junk could maybe be eliminated.
# TODO: Should be portable. Rename MeaningLessFile to MeaninglessFile.
# Or rather make it an option.
def MeaningLessFile(path):
	if lib_util.isPlatformWindows:
		return False

	# Some files are not interesting at all.
	# TODO: Horrible hard-code for testing only !!!!!!!!!!!!!!!!
	if ( path == "/home/rchateau/.xsession-errors" ):
		return 1

	# We could also check if this is really a shared library.
	# file /lib/libm-2.7.so: ELF 32-bit LSB shared object etc...
	if path.endswith(".so"):
		return True

	# Not sure about "M" and "I". Also: Should precompile regexes.
	for rgx in [ r'/lib/.*\.so\..*', r'/usr/lib/.*\.so\..*' ] :
		if re.match( rgx, path, re.M|re.I):
			return True

	for start in [ '/usr/share/locale/', '/usr/share/fonts/', '/etc/locale/', '/var/cache/fontconfig/', '/usr/lib/jvm/' ] :
		if path.startswith( start ):
			return True

	return False

################################################################################
try:
	from urllib.request import urlopen
except ImportError:
	from urllib import urlopen

# TODO: Avoids creation of a temporary file.
def Url2Grph(grph,url,logfi = None):
	if logfi == None:
		logfi = sys.stderr
	logfi.write( "Url2Grph url=%s\n" % Url2Grph )
	try:
		# Horrible hardcode, temporary.
		if sys.version_info >= (3,1,) and sys.version_info < (3,3,) :
			# ZUT !!! VOILA CE QUI ARRIVE AVEC DES REDIRECTIONS.
			#Unexpected type '<class 'bytes'>' for source 'b'<!DOCTYPE html>\n
			content = urlopen(url).read()
			result = grph.parse(content.decode('utf8'))

		else:
			# TODO: GET RID OF THIS TEMP FILE AND USE urlopen()
			tmpfilObj = TmpFile("url2graph","rdf")
			tmpfil = tmpfilObj.Name
			logfi.write( "Url2Grph tmpfil=%s\n" % tmpfil )

			# TODO: Maybe this is an error message in HTML instead of a RDF document.
			if sys.version_info >= (3,):
				urllib.request.urlretrieve (url, tmpfil)
			else:
				urllib.urlretrieve (url, tmpfil)
			grph.parse(tmpfil)
	# Can be: xml.sax._exceptions.SAXParseException:
	# Maybe this is a HTML file because of an error.
	# If so, display the content.
	except Exception:
		exc = sys.exc_info()[1]
		errmsg = "Url2Grph v=" + str(sys.version_info) + " Error url=" + url + " EXC=" + str(exc)
		logfi.write("Err=[%s]\n" % (errmsg) )
		ErrorMessageHtml( errmsg )


# http://127.0.0.1/Survol/htbin/objtypes_wmi.py?xid=\\rchateau-HP\root\Cli%3A.
#
		
################################################################################
def Url2Svg(url_rdf):
	return lib_util.uriRoot + '/internals/gui_create_svg_from_several_rdfs.py?dummy=none&url=' + lib_util.EncodeUri( url_rdf )

################################################################################
def KillProc(pid):
	sys.stderr.write("About to kill pid=" + str(pid) )
	try:
		# SIGQUIT apparently not defined on Windows.
		if lib_util.isPlatformLinux:
			os.kill( pid, signal.SIGQUIT )
		else:
			# On Linux, it raises: KeyboardInterrupt
			os.kill( pid, signal.SIGINT )

	except AttributeError:
		exc = sys.exc_info()[1]
		# 'module' object has no attribute 'SIGQUIT'
		sys.stderr.write("Caught:"+str(exc)+" when killing pid=" + str(pid) )
	except Exception:
		# For example: [Errno 3] No such process.
		exc = sys.exc_info()[1]
		sys.stderr.write("Unknown exception " + str(exc) + " when killing pid=" + str(pid) )

################################################################################

def JoinThreads(threads):
	sys.stderr.write("Waiting\n")
	for thread in threads:
		sys.stderr.write('Joining %s\n' % thread.getName())
		thread.join()

def GetHost(addr):
	try:
		return socket.gethostbyaddr(addr)
	except socket.herror:
		return [ addr, [] ]

def SocketToPair(connect):
	if sys.version_info >= (3,):
		larray = connect.local_address
		rarray = connect.remote_address
	else:
		larray = connect.laddr
		rarray = connect.raddr
	return (larray,rarray)

# This asynchronously adds a RDF relation between a process and a socket.
# As it is asychronous, we can make a DNS query.
class PsutilAddSocketThread(threading.Thread):
	def __init__(self, node_process,connect,grph,grph_lock):
		self.node_process = node_process
		self.connect = connect
		self.grph = grph
		self.grph_lock = grph_lock

		threading.Thread.__init__(self)

	# TODO: We might, in the future, have one single object instead of two.
	# For example "socket_pair". Not sure.
	def run(self):
		# Now we create a node in rdflib, and we need a mutex for that.
		try:
			self.grph_lock.acquire()
			( larray, rarray ) = SocketToPair(self.connect)

			lhost = GetHost(larray[0])[0]
			lsocketNode = gUriGen.AddrUri( lhost, larray[1] )

			try:
				rhost = GetHost(rarray[0])[0]
				rsocketNode = gUriGen.AddrUri( rhost, rarray[1] )
				self.grph.add( ( lsocketNode, pc.property_socket_end, rsocketNode ) )
			except IndexError:
				pass
	
			# PAS CERTAIN: Qu'est ce qui dit qu une des sockets aboutit au host ?
			self.grph.add( ( self.node_process, pc.property_has_socket, lsocketNode ) )
			self.grph.add( ( lsocketNode, pc.property_information, rdflib.Literal(self.connect.status) ) )
		finally:
			self.grph_lock.release()
		# Some throttling, in case there are thousands of nodes.
		time.sleep(0.001)

def PsutilAddSocketToGraphAsync(node_process,connects,grph):
	threadsArr = []
	grph_lock = threading.Lock()

	for cnt in connects:
		if( ( cnt.family == 2 )
		and ( cnt.type == 1 )
		# and ( cnt.status == 'ESTABLISHED' )
		):
			thr = PsutilAddSocketThread( node_process, cnt, grph, grph_lock )
			thr.start()
			threadsArr.append( thr )

	JoinThreads(threadsArr)

# TODO: We might, in the future, have one single object instead of two.
# TODO: Remove this hardcode !!!
# For example "socket_pair". Not sure.
def PsutilAddSocketToGraphOne(node_process,connect,grph):
	# sys.stdout.write('    ')
	if( ( connect.family == 2 )
	and ( connect.type == 1 )
	# and ( connect.status == 'ESTABLISHED' )
	):
		# Not sure of this test, maybe this rather depends on the psutil version.
		if sys.version_info >= (3,):
			lsocketNode = gUriGen.AddrUri( connect.local_address[0], connect.local_address[1] )
			try:
				rsocketNode = gUriGen.AddrUri( connect.remote_address[0], connect.remote_address[1] )
			except IndexError:
				rsocketNode = None
		else:
			lsocketNode = gUriGen.AddrUri( connect.laddr[0], connect.laddr[1] )
			try:
				rsocketNode = gUriGen.AddrUri( connect.raddr[0], connect.raddr[1] )
			except IndexError:
				rsocketNode = None

		# Il faudrait plutot une relation commutative.
		if rsocketNode != None:
			grph.add( ( lsocketNode, pc.property_socket_end, rsocketNode ) )

		# PAS CERTAIN: Qu'est ce qui dit qu une des sockets aboutit au host ?
		grph.add( ( node_process, pc.property_has_socket, lsocketNode ) )
		grph.add( ( lsocketNode, pc.property_information, rdflib.Literal(connect.status) ) )

# On va peut-etre se debarrasser de ca si la version asynchrone est plus-rapide.
def PsutilAddSocketToGraph(node_process,connects,grph):
	for cnt in connects:
		PsutilAddSocketToGraphOne(node_process,cnt,grph)

################################################################################
# Reformat the username because in psutil.users() it is "Remi",
# but from process.username(), it is "PCVERO\Remi"
#
# http://msdn.microsoft.com/en-gb/library/windows/desktop/aa380525(v=vs.85).aspx
# User principal name (UPN) format is used to specify an Internet-style name,
# such as UserName@Example.Microsoft.com.
#
# The down-level logon name format is used to specify a domain
# and a user account in that domain, for example, DOMAIN\UserName.
# The following table summarizes the parts of a down-level logon name.
#
# Some say that: UserName@DOMAIN also works.
# 
# http://serverfault.com/questions/371150/any-difference-between-domain-username-and-usernamedomain-local
def FormatUser(usrnam):
	# BEWARE: WE ARE LOSING THE DOMAIN NAME.
	shortnam = usrnam.split('\\')[-1]

	# return shortnam + "@" + lib_util.currentHostname
	return shortnam

################################################################################
# How to display RDF files ?
#
# <?xml version="1.0" encoding="iso-8859-1"?>
# <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
# <html> 
#
# And the XSL file might contain something like:
# <?xml version="1.0" encoding="iso-8859-1"?>
# <actu xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="schema.xsd">
# <?xml-stylesheet type="text/xsl" href="fichier.xsl"?>
# <article rubrique="fiscal" dateArticle="03/11/09" idArticle="art3200">
# <copyright>..... 

# Avec la geolocalisation des adresses IP, on pourrait fabriquer des fichers KML.

################################################################################


# Premier bug: Dans file_directory, les sous-noeuds correspondant aux scripts
# ne pointent pas vers leur parent.

################################################################################

# http://www.graphviz.org/Gallery/directed/cluster.html

# Pour tirer parti des blocs (sous-reseaux) dans graphviz, on pourrait regrouper
# des objets qui ont une propriete commune (Threads d un process,
# fichiers dans un dir, de facon recursive, methodes dans une classe),
# Ca evite meme de devoir tracer des aretes !!!
# ou tout simplement le host, comme container: subgraphes, clusters.