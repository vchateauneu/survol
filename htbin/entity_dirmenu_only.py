#!/usr/bin/python

"""
Scripts hierarchy
"""

import os
import re
import sys
import psutil
import rdflib
import lib_util
import lib_common
from lib_properties import pc

# This script is used by entity.py as a module, but also as a script with the CGI parameter mode=menu,
# by the D3 interface, to build contextual right-click menu.

def TestUsability(importedMod,entity_type,entity_ids_arr):
	try:
		isUsable = importedMod.Usable(entity_type,entity_ids_arr)
	except AttributeError:
		return None

	# sys.stderr.write("Module %s : %d\t" %(argFil,isUsable	))
	if isUsable:
		return None

	errorMsg = importedMod.Usable.__doc__
	if not errorMsg:
		errorMsg = importedMod.__name__ + " not usable"
		if not errorMsg:
			errorMsg = "No message"
	return errorMsg

# TODO: CharTypesComposer

# This is used for debugging only.
def DirMenuReport(depthCall,strMsg):
	txtMargin = ( "    " * depthCall )
	sys.stderr.write(txtMargin + strMsg)

# TODO: Only return json data, and this script will only return json, nothing else.
def DirToMenu(grph,parentNode,entity_type,entity_id,is_host_remote,flagShowAll):
	encodedEntityId=lib_util.EncodeUri(entity_id)
	entity_ids_arr = lib_util.EntityIdToArray( entity_type, entity_id )

	if entity_type:
		# entity_type might contain a slash, for example: "sqlite/table"
		relative_dir = "/sources_types/" + entity_type
	else:
		relative_dir = "/sources_types"

	directory = lib_util.gblTopScripts + relative_dir

	DirToMenuAux(grph,parentNode,directory,relative_dir,entity_type,entity_ids_arr,encodedEntityId,is_host_remote,flagShowAll,depthCall = 1)



# This lists the scripts and generate RDF nodes.
# Returns True if something was added.
def DirToMenuAux(grph,parentNode,curr_dir,relative_dir,entity_type,entity_ids_arr,encodedEntityId,is_host_remote,flagShowAll,depthCall = 1):
	# DirMenuReport( depthCall, "curr_dir=%s relative_dir=%s\n"%(curr_dir,relative_dir))
	# In case there is nothing.
	dirs = None
	for path, dirs, files in os.walk(curr_dir):
		break

	# Maybe this class is not defined in our ontology.
	if dirs == None:
		# sys.stderr.write("No content in "+curr_dir)
		return False

	# Will still be None if nothing is added.
	rdfNode = None
	sub_path = path[ len(curr_dir) : ]

	relative_dir_sub_path = relative_dir + sub_path

	argDir = relative_dir_sub_path.replace("/",".")[1:]

	# Maybe there is a usability test in the current module.
	# The goal is to control all scripts in the subdirectories, from here.
	try:
		entity_class = ".".join( relative_dir.split("/")[2:] )
		# DirMenuReport( depthCall, "entity_class=%s\n"%(entity_class))

		importedMod = lib_util.GetEntityModule(entity_class)
		if importedMod:
			errorMsg = TestUsability(importedMod,entity_type,entity_ids_arr)
			# if flagShowAll and errorMsg ???
			if errorMsg:
				# Surprisingly, the message is not displayed as a subdirectory, but in a separate square.
				grph.add( ( parentNode, lib_common.MakeProp("Usability"), rdflib.Literal(errorMsg) ) )
				return False
	except IndexError:
		# If we are at the top-level, no interest for the module.
		pass


	containsSomething = False
	for dir in dirs:
		# DirMenuReport( depthCall, "dir=%s\n"%(dir))
		# Might be generated by our Python interpreter.
		if dir == "__pycache__":
			continue

		full_sub_dir = curr_dir + "/" + dir
		full_sub_dir = full_sub_dir.replace("\\","/")

		currDirNode = lib_util.DirDocNode(argDir,dir)

		if not currDirNode:
			DirMenuReport( depthCall, "currDirNode NONE: argDir=%s dir=%s\n"%(argDir,dir))
			continue

		sub_relative_dir = relative_dir + "/" + dir

		sub_entity_class = ".".join( sub_relative_dir.split("/")[2:] )
		ontoKeys = lib_util.OntologyClassKeys(sub_entity_class)
		# DirMenuReport( depthCall, "Checked ontology of %s: ontoKeys=%s\n"%(sub_entity_class,str(ontoKeys)))

		# TODO: Beware, if not ontology, returns empty array. Why not returning None ?
		if ontoKeys != []:
			# DirMenuReport( depthCall, "Module %s has an ontology so it is a class. Skipping\n"%(sub_relative_dir))
			# BEWARE: NO MORE DEFAULT ONTOLOGY ["Id"]
			continue

		somethingAdded = DirToMenuAux(grph,currDirNode, full_sub_dir,sub_relative_dir,entity_type,entity_ids_arr,encodedEntityId,is_host_remote,flagShowAll,depthCall + 1)
		# This adds the directory name only if it contains a script.
		if somethingAdded:
			# CA MARCHE DANS LES DEUX CAS. SI PROPRIETE DIFFERENTE, ON AURA SIMPLEMENT DEUX PAVES, UN POUR LES DIR, L AUTRE POUR LES FICHIERS.
			# grph.add( ( parentNode, pc.property_directory, currDirNode ) )
			grph.add( ( parentNode, pc.property_rdf_data1, currDirNode ) )
		containsSomething = containsSomething | somethingAdded

	for fil in files:
		# We want to list only the usable Python scripts.
		if not fil.endswith(".py") or fil == "__init__.py":
			continue

		script_path = relative_dir_sub_path + "/" + fil

		# DirMenuReport( depthCall, "DirToMenu encodedEntityId=%s\n" % encodedEntityId)
		if is_host_remote:
			genObj = lib_common.RemoteBox(entity_host)
		else:
			genObj = lib_common.gUriGen

		url_rdf = genObj.MakeTheNodeFromScript( script_path, entity_type, encodedEntityId )

		errorMsg = None

		try:
			importedMod = lib_util.GetScriptModule(argDir, fil)
		except Exception:
			errorMsg = sys.exc_info()[1]
			DirMenuReport( depthCall, "Cannot import=%s. Caught: %s\n" % (script_path, errorMsg ) )
			importedMod = None
			if not flagShowAll:
				continue

		if not errorMsg:
			# Show only scripts which want to be shown. Each script can have an optional function
			# called Usable(): If it is there and returns False, the script is not displayed.
			errorMsg = TestUsability(importedMod,entity_type,entity_ids_arr)

		if not flagShowAll and errorMsg:
			continue

		# If the entity is on another host, does this work on remote entities ?
		if is_host_remote:
			try:
				# Script can be used on a remote entity.
				can_process_remote = importedMod.CanProcessRemote
			except AttributeError:
				can_process_remote = False

			if not can_process_remote:
				if not errorMsg:
					errorMsg = "%s is local" % ( argFil[1:] )
				DirMenuReport( depthCall, "Script %s %s cannot work on remote entities: %s at %s\n" % ( currentModule, argFil, entity_id , entity_host ) )

				if not flagShowAll:
					continue

		# Here, we are sure that the script is added.
		# TODO: If no script is added, should not add the directory?
		rdfNode = rdflib.term.URIRef(url_rdf)
		grph.add( ( parentNode, pc.property_rdf_data1, rdfNode ) )

		# Default doc text is file name minus the ".py" extension.
		nodModu = lib_util.FromModuleToDoc(importedMod,fil[:-3])

		grph.add( ( rdfNode, pc.property_information, nodModu ) )

		if errorMsg:
			grph.add( ( rdfNode, lib_common.MakeProp("Error"), rdflib.Literal(errorMsg) ) )

	# This tells if a script was added in this directory or one of the subdirs.
	return ( rdfNode is not None ) | containsSomething

################################################################################



# Si entity_type != "" mais entity_id == "", ca n'a pas de sens
# d'afficher les scripts du directory htbin/sources/<type>
# car on n'a pas d'id. En revanche, on pourrait afficher selectivement
# des scripts dans "top" qui affichent toutes les entites de ce type.
# Ca revient a selectionner certains scripts.
# On peut faire ca grossierement en filtrant sur le nom.
# Mais on voudrait en fait les afficher directement.
# On peut donc avoir des scripts appeles top/<type>.index.xyzw.py .
# Mais on voudrait en avoir plusieurs, eventuellement.




def Main():

	paramkeyShowAll = "Show all scripts"

	# This can process remote hosts because it does not call any script, just shows them.
	cgiEnv = lib_common.CgiEnv(
					can_process_remote = True,
					parameters = { paramkeyShowAll : False })
	entity_id = cgiEnv.m_entity_id
	entity_host = cgiEnv.GetHost()
	flagShowAll = int(cgiEnv.GetParameters( paramkeyShowAll ))

	( nameSpace, entity_type, entity_namespace_type ) = cgiEnv.GetNamespaceType()

	is_host_remote = not lib_util.IsLocalAddress( entity_host )

	sys.stderr.write("entity: entity_host=%s entity_type=%s entity_id=%s is_host_remote=%r\n" % ( entity_host, entity_type, entity_id, is_host_remote ) )

	# It is simpler to have an empty entity_host, if possible.
	# CHAIS PAS. EN FAIT C EST LE CONTRAIRE, IL FAUT METTRE LE HOST
	if not is_host_remote:
		entity_host = ""

	grph = rdflib.Graph()

	rootNode = lib_util.RootUri()

	if entity_id != "" or entity_type == "":
		entity_ids_arr = lib_util.EntityIdToArray( entity_type, entity_id )

		# TODO: Plutot qu'attacher tous les sous-directory a node parent,
		# ce serait peut-etre mieux d'avoir un seul lien, et d'afficher
		# les enfants dans une table, un record etc...
		# OU: Certaines proprietes arborescentes seraient representees en mettant
		# les objets dans des boites imbriquees: Tables ou records.
		# Ca peut marcher quand la propriete forme PAR CONSTRUCTION
		# un DAG (Direct Acyclic Graph) qui serait alors traite de facon specifique.
		DirToMenu(grph,rootNode,entity_type,entity_id,is_host_remote,flagShowAll)

	cgiEnv.OutCgiRdf(grph, "LAYOUT_RECT", [pc.property_directory,pc.property_rdf_data1])

if __name__ == '__main__':
	Main()

