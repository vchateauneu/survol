#!/usr/bin/python

"""
Overview
"""

import os
import re
import sys
import psutil
import rdflib

# With Linux, Python2 and cgiserver, it can import it,
# but after that it cannot "import lib_common"
import lib_util
import lib_common
from lib_properties import pc

from sources_types import CIM_Process
from sources_types import CIM_ComputerSystem

################################################################################

# WHAT TO DO WITH THE HOST ???????
# This should not be the same scripts:
# Some "normal" scripts are able to use a hostname, but this is very rare.
# CgiEnv is able to say that. Also, this must be stored in the info cache.
# If we take the entity_id from CgiEnv without explicitely saying
# that the current script can process the hostname, then it is an error.
# Also: This is where we need to "talk" to the other host ?
# And we must display the node of the host as seen from the local machine.


# TODO: CharTypesComposer
# Actuellement on parcourt toute l'arborescence et on affiche tous les scripts
# a partir d un directory. Ne pas descendre dans les sous-directories s'il y a un sous-type.
# Mais le faire quand meme si le decoupage est plutot un namespace.
# Comment a la fois utiliser des sous-directories comme types derives
# et comme namespaces ?
# Dans le directory principal, on peut n avoir que des names-spaces
# car un sous-type n a pas de sens. Et on affichera recursivement.
# Toutefois pour le directory des types,
# il faut descendre dans les namespaces mais pas dans les sous-types.
# En fait, pour travailleur naturellement, il faudrait inverser la hierarchie:
# Que les sous-types pointent vers les types.
# Peut-etre mettre dans le __init__.py du directory d'un sous-type,
# une reference vers le type de base. Ou bien se servir du nom ?
# Avec le separateur un sous-type contiendrait la liste de ses types de base ?

# On peut aussi donner une syntaxe specifique aux sous-directory namespaces,
# et DirToMenu ne descendra dans les sous-dir que si namespaces.
# Ou bien: Chaque directory contient dans le __init__.py
# une fonction qui dit si on peut afficher ou non:
# Cette fonction prend en parametre le entity_type, os.platform.
# Seul inconvenient:
#  - Il faut assigner un role a la classe de base, qui sert de directory de depart.
#  - La classe de base sert aussi pour la liste des parametres et les couleurs.
#  - Confusions classe de base et namespace: "oracle,table" et "mysql,table"
#    Valable pour les couleurs (Ca sert d avoir une couleur commune a tous
#    les objets d un meme namespace) mais pas pour les parametres evidemment.
#    Autre confusion si namespaces et classes de base ont la meme structure:
#    - Impossible d'apparier les hierarchies avec WBEM et WMI. Par exemple on pourrait
#    deriver localement de CIM_Process.
#    - Pourrait-on representer la hierarchie user/CIM_Account et user/LMI_Account ?
# Si on melange sous-types et namespaces, on descend toujours dans les dir des namespaces
# si la fonction de __init__.py le permet ? Probleme: le nom du type pourrait etre:
# "linux,file,dir" ou "windows,file,dir" ? ou "file,linux,symlink" ?
# Ou bien que "symlink" et on parcourerait toujours l arborescence ?
# Non: Le nom de la sous-classe doit toujours comporter le namespace.
# OU ALORS: Si namespace, c'est une hierachie a part:
# portable/sources_types/file/dir
# portable/sources_top/file/dir
# oracle/sources_types/table
# linux/sources_types/user
# windows_com/enumerate.Win32_Process
# Avantage: On deplace un namespace en copiant uniquement un directory.
# Et meme pourquoi ne pas reutiliser la syntaxe des sous-classes de WMI et WBEM ?

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

def DirMenuReport(depthCall,strMsg):
	txtMargin = ( "    " * depthCall )
	sys.stderr.write(txtMargin + strMsg)

# This lists the scripts and generate RDF nodes.
# Returns True if something was added.
def DirToMenu(grph,parentNode,curr_dir,relative_dir,depthCall = 1):
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

		somethingAdded = DirToMenu(grph,currDirNode, full_sub_dir,sub_relative_dir, depthCall + 1)
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


def CurrentUser():
	currProc = psutil.Process(os.getpid())
	return CIM_Process.PsutilProcToUser(currProc)

def AddDefaultScripts(grph,rootNode,entity_host):
	nodeObjTypes = rdflib.term.URIRef( lib_util.uriRoot + '/objtypes.py' )
	grph.add( ( rootNode, pc.property_rdf_data_nolist2, nodeObjTypes ) )

	# Gives a general access to WBEM servers. In fact we might iterate on several servers, or none.
	nodePortalWbem = lib_util.UrlPortalWbem(entity_host)
	grph.add( ( rootNode, pc.property_rdf_data_nolist2, nodePortalWbem ) )

	# Gives a general access to WMI servers.
	nodePortalWmi = lib_util.UrlPortalWmi(entity_host)
	grph.add( ( rootNode, pc.property_rdf_data_nolist2, nodePortalWmi ) )

	currentNodeHostname = lib_common.gUriGen.HostnameUri( lib_util.currentHostname )
	grph.add( ( currentNodeHostname, pc.property_information, rdflib.Literal("Current host:"+lib_util.currentHostname) ) )
	grph.add( ( rootNode, pc.property_rdf_data_nolist2, currentNodeHostname ) )

	currUsername = CurrentUser()
	currentNodeUser = lib_common.gUriGen.UserUri( currUsername )
	grph.add( ( currentNodeUser, pc.property_information, rdflib.Literal("Current user:"+currUsername) ) )
	grph.add( ( rootNode, pc.property_rdf_data_nolist2, currentNodeUser ) )

################################################################################

#Un module est defini par son ontologie:
#Quand on itere sur des directories et sous-directories pour en afficher les scripts,
#il suffit de s'assurer que chaque sous-module a la meme ontologie que le point de depart
#(On bien n a pas d ontologie, bref, que ce soit coherent avec le point de depart.)
# De meme dans sources_top: On devrait aller chercher dans scripts_types,
# les scripts qui n ont pas d'ontologie.
# Dans entity.py, comme on a une entite (la machine courante),
# on peut aller chercher les scripts qui ont une ontologie pour ces classes.

# On prend l ontologie du niveau courant ou on se trouve,
# donne par la entity_class.
# Si y en a pas (sources_top) et ben y en a pas.
# Ensuite on liste recursivement les fichiers mais des que l ontologie change,
# c est a dire, si une ontologie est definie dans un module intermediaire.
# (Ce qu on voit en chargeant le module implicitement) alors on laisse tomber)

# En plus, dans le entity par defaut, comme on a forcement un user et une machine,
# on va chercher les scripts de ces deux entites.

# Probleme: On doit aller chercher toutes les entites, charger tous les modules.

################################################################################

def Main():
	# They are defined global so that DirToMenu can access them without code change.
	global is_host_remote
	global entity_type
	global entity_id
	global encodedEntityId
	global entity_host
	global entity_ids_arr
	global flagShowAll

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


	if entity_type:
		# entity_type might contain a slash, for example: "sqlite/table"
		relative_dir = "/sources_types/" + entity_type
	else:
		relative_dir = "/sources_types"

	# sys.stderr.write("entity: lib_util.gblTopScripts=%s relative_dir=%s\n" % ( lib_util.gblTopScripts, relative_dir ) )

	directory = lib_util.gblTopScripts + relative_dir

	grph = rdflib.Graph()

	rootNode = lib_util.RootUri()

	if entity_id != "" or entity_type == "":
		entity_ids_arr = lib_util.EntityIdToArray( entity_type, entity_id )

		# Each entity type ("process","file" etc... ) can have a small library
		# of its own, for displaying a rdf node of this type.
		if entity_type:
			entity_module = lib_util.GetEntityModule(entity_type)
			if entity_module:
				try:
					entity_module.AddInfo( grph, rootNode, entity_ids_arr )
				except AttributeError:
					exc = sys.exc_info()[1]
					sys.stderr.write("No AddInfo for %s %s: %s\n"%( entity_type, entity_id, str(exc) ))
		else:
			sys.stderr.write("No lib_entities for %s %s\n"%( entity_type, entity_id ))

		encodedEntityId=lib_util.EncodeUri(entity_id)

		# TODO: Plutot qu'attacher tous les sous-directory a node parent,
		# ce serait peut-etre mieux d'avoir un seul lien, et d'afficher
		# les enfants dans une table, un record etc...
		# OU: Certaines proprietes arborescentes seraient representees en mettant
		# les objets dans des boites imbriquees: Tables ou records.
		# Ca peut marcher quand la propriete forme PAR CONSTRUCTION
		# un DAG (Direct Acyclic Graph) qui serait alors traite de facon specifique.
		DirToMenu(grph,rootNode,directory,relative_dir)

	if entity_type != "":
		CIM_ComputerSystem.AddWbemWmiServers(grph,rootNode, entity_host, nameSpace, entity_type, entity_id)

	AddDefaultScripts(grph,rootNode,entity_host)

	cgiEnv.OutCgiRdf(grph, "LAYOUT_RECT", [pc.property_directory,pc.property_rdf_data1])

if __name__ == '__main__':
	Main()

