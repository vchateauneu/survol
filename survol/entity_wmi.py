#!/usr/bin/python

"""
WMI instance
"""

import sys
import lib_common
import lib_wmi
import lib_util

try:
	import wmi
except ImportError:
	lib_common.ErrorMessageHtml("WMI Python library not installed")

def WmiReadWithMoniker( cgiEnv, cgiMoniker ):
	"""
		This returns an array of the single object read wrom WMI with the moniker.
		Or null if no such object exists.
	"""
	try:
		objWmi = wmi.WMI(moniker=cgiMoniker,find_classes=False)
		return [ objWmi ]
	except Exception:
		exc = sys.exc_info()[1]
		sys.stderr.write("cgiMoniker=%s Caught:%s\n" % ( cgiMoniker, str(exc) ) )
		return None

def WmiReadWithQuery( cgiEnv, connWmi, className ):
	"""
		Maybe reading with the moniker does not work because not all properties.
		This splits the moniker into key value paris, and uses a WQL query.
	"""
	splitMonik = lib_util.SplitMoniker( cgiEnv.m_entity_id )
	aQry = lib_util.SplitMonikToWQL(splitMonik,className)

	try:
		return connWmi.query(aQry)
	except Exception:
		exc = sys.exc_info()[1]
		lib_common.ErrorMessageHtml("Query=%s Caught:%s" % ( aQry, str(exc) ) )

# Add all usual Python types.
scalarDataTypes = lib_util.six_string_types + ( lib_util.six_text_type, lib_util.six_binary_type ) + lib_util.six_integer_types


# This is a hard-coded list of properties which cannot be displayed.
# They should be stored in the class directory.
prpCannotBeDisplayed = {
	# TODO: Convert this into an image.
	"CIM_ComputerSystem" : ["OEMLogoBitmap"]
}

def DispWmiProperties(grph,wmiInstanceNode,objWmi,displayNoneValues,className,mapPropUnits):
	"""
		Displays the properties of a WMI object (Not a class),
		then sticks them to the WMI object node.
	"""

	for prpName in objWmi.properties:
		prpProp = lib_common.MakeProp(prpName)

		try:
			valUnit = mapPropUnits[prpName]
		except KeyError:
			valUnit = ""

		# CIM_ComputerSystem
		try:
			doNotDisplay = prpName in prpCannotBeDisplayed[className]
		except KeyError:
			doNotDisplay = False

		if doNotDisplay:
			sys.stderr.write("Cannot display:%s\n"%str(getattr(objWmi,prpName)))
			value = "Cannot be displayed"
		else:
			# BEWARE, it could be None.
			value = getattr(objWmi,prpName)

		# Some specific properties match a Survol class,
		# so it is possible to add a specific node.
		# THIS WORKS BUT IT IS NOT NICE, AS A SEPARATE NODE.
		# We would like to have a clickable URL displayed in a table TD.
		if prpName == "GUID":
			# Example: "{CF185B35-1F88-46CF-A6CE-BDECFBB59B4F}"
			nodeGUID = lib_common.gUriGen.ComTypeLibUri( value )
			grph.add( ( wmiInstanceNode, prpProp, nodeGUID ) )
			continue

		if isinstance( value, scalarDataTypes ):
			# Special backslash replacement otherwise:
			# "NT AUTHORITY\\\\NetworkService" displayed as "NT AUTHORITYnd_0etworkService"
			# TODO: Why not CGI escaping ?
			valueReplaced = str(value).replace('\\','\\\\')

			if valUnit:
				valueReplaced = lib_util.AddSIUnit( valueReplaced, valUnit )
			grph.add( ( wmiInstanceNode, prpProp, lib_common.NodeLiteral( valueReplaced ) ) )
		elif isinstance( value, ( tuple) ):
			# Special backslash replacement otherwise:
			# "NT AUTHORITY\\\\NetworkService" displayed as "NT AUTHORITYnd_0etworkService"
			# TODO: Why not CGI escaping ?
			tupleReplaced = [ str(oneVal).replace('\\','\\\\') for oneVal in value ]

			# tuples are displayed as tokens separated by ";". Examples:
			#
			# CIM_ComputerSystem.OEMStringArray
			#" ABS 70/71 60 61 62 63; ;FBYTE#2U3E3X47676J6S6b727H7M7Q7T7W7m8D949RaBagapaqb3bmced3.fH;; BUILDID#13WWHCHW602#SABU#DABU;"
			#
			# CIM_ComputerSystem.Roles
			# "LM_Workstation ; LM_Server ; SQLServer ; NT ; Potential_Browser ; Master_Browser"
			cleanTuple = " ; ".join( tupleReplaced )
			grph.add( ( wmiInstanceNode, prpProp, lib_common.NodeLiteral( cleanTuple ) ) )
		elif value is None:
			if displayNoneValues:
				grph.add( ( wmiInstanceNode, prpProp, lib_common.NodeLiteral( "None" ) ) )
		else:
			try:
				refMoniker = str( value.path() )
				refInstanceUrl = lib_util.EntityUrlFromMoniker( refMoniker )
				refInstanceNode = lib_common.NodeUrl(refInstanceUrl)
				grph.add( ( wmiInstanceNode, prpProp, refInstanceNode ) )
			except AttributeError:
				exc = sys.exc_info()[1]
				grph.add( ( wmiInstanceNode, prpProp, lib_common.NodeLiteral( str(exc) ) ) )

def ImportSurvolModuleFromWmiClass(connWmi, className):
	allBaseClasses = ( className, ) + lib_wmi.WmiBaseClasses(connWmi, className)
	for theClassAscending in allBaseClasses:
		# Maybe there is a module without ontology.
		# In this case, try a base class. This is what does this function.
		ontoKeys = lib_util.OntologyClassKeys(theClassAscending)
		if len(ontoKeys):
			return ( theClassAscending, ontoKeys )
	return None,None

def AddSurvolObjectFromWmi(grph,wmiInstanceNode,connWmi,className,objList):
	"""
		Must find the url of the object in the Survol terminoloy equivalent to this one in WMI.
		This does not care the namespace which is set to root/cimv2 anyway.
		The reason is that it is the most common one, and the others seem to be used
		for very technical purpose.
	"""

	# The first step is to iterate on the base classes until there is one of the Survol classes.
	( survolEquivalentClass, ontoKeys ) = ImportSurvolModuleFromWmiClass(connWmi, className)

	# This class nor any of its base classes exists in Survol.
	if survolEquivalentClass is None:
		return

	setSurvolUrls = set()

	for objWmi in objList:
		# sys.stderr.write("objWmi=[%s]\n" % str(objWmi) )

		propValuesArray = []

		# For each property of the survol ontology, picks the value returned by WMI.
		# Replace missing values by an empty string.
		for survKey in ontoKeys:
			try:
				wmiVal = getattr(objWmi,survKey)
			except KeyError:
				sys.stderr.write("AddSurvolObjectFromWmi className=%s no value for key=%s\n"%(className,survKey))
				wmiVal = ""
			propValuesArray.append(wmiVal)

		entityModule = lib_util.GetEntityModule(survolEquivalentClass)

		# Maybe there is a special function for encoding these arguments.
		try:
			urlSurvol = entityModule.MakeUri(*propValuesArray)
		except:
			# Otherwise, general case.
			urlSurvol = lib_common.gUriGen.UriMake(survolEquivalentClass,*propValuesArray)

		setSurvolUrls.add(urlSurvol)

	# There might potentially be several Survol objects for these several WMI objects.
	# It depends on the properties, as Survol takes only a subset of them.
	propWmi2Survol = lib_common.MakeProp("WMI equivalent")
	for urlSurvol in setSurvolUrls:
		grph.add( ( wmiInstanceNode, propWmi2Survol, urlSurvol ) )
	return


# Better use references() because it gives much more information.
#for assoc in objWmi.associators():
#	assocMoniker = str( assoc.path() )
#	sys.stderr.write("assocMoniker=[%s]\n" % assocMoniker )
#	assocInstanceUrl = lib_util.EntityUrlFromMoniker( assocMoniker )
#	assocInstanceNode = lib_common.NodeUrl(assocInstanceUrl)
#	grph.add( ( wmiInstanceNode, lib_common.MakeProp("assoc"), assocInstanceNode ) )

# TESTS:
# OK
# wmi.WMI(moniker='root\CIMV2:CIM_ComputerSystem.Name="rchateau-hp"')
# _wmi_object: \\RCHATEAU-HP\root\CIMV2:Win32_ComputerSystem.Name="rchateau-hp">
# KAPUTT
# wmi.WMI(moniker='\\rchateau-HP\root\CIMV2:CIM_ComputerSystem.Name="rchateau-hp"')
# wmi.WMI(moniker='root\CIMV2:CIM_ComputerSystem.Name=rchateau-hp')
# wmi.WMI(moniker='root\CIMV2:CIM_ComputerSystem.Name="127.0.0.1"')



# WmiExplorer displays the namespace as: "ROOT\CIMV2"
#
# The namespace is converted to lowercase, no idea why.
# https://msdn.microsoft.com/en-us/library/windows/desktop/aa389766%28v=vs.85%29.aspx
# The __Namespace system class has a single property called Name,
# which must be unique within the scope of the parent namespace.
# The Name property must also contain a string that begins with a letter.
# All other characters in the string can be letters, digits, or underscores.
# All characters are case-insensitive.
# refMoniker='\\RCHATEAU-HP\root\cimv2:CIM_DataFile.Name="c:\\windows\\system32\\sspicli.dll"'
# cgiMoniker='\\RCHATEAU-HP\root\CIMV2:CIM_DataFile.Name="c:\\windows\\system32\\sspicli.dll"'
#
# '\\RCHATEAU-HP\root\cimv2:Win32_UserAccount.Domain="RCHATEAU-HP",Name="Administrator"'
# '\\RCHATEAU-HP\root\cimv2:Win32_UserAccount.Domain="rchateau-HP",Name="Administrator"'
#
def EqualMonikers( monikA, monikB ):
	splitA = monikA.split(':')
	splitB = monikB.split(':')

	# Maybe we could simply make a case-insensitive string comparison.
	return splitA[0].upper() == splitB[0].upper() and splitA[1:].upper() == splitB[1:].upper()

# Dont do this on a Win32_ComputerSystem object and several other classes; it is VERY SLOW !
# TODO: Test with a small data set.
def DispWmiReferences(grph,wmiInstanceNode,objWmi,cgiMoniker):
	for objRef in objWmi.references():
		literalKeyValue = dict()
		refInstanceNode = None
		for keyPrp in objRef.properties:
			valPrp = getattr(objRef,keyPrp)
			try:
				# references() have one leg pointing to the current object,
				refMoniker = str( valPrp.path() )

				# Maybe it would be better to compare the objects ???
				if not EqualMonikers( refMoniker, cgiMoniker ):
					# TODO: Disabled for the moment because we do not understand the logic.
					if False and refInstanceNode is not None:
						# TODO: Pourquoi ceci ????????????
						# Inconsistency:\\RCHATEAU-HP\root\cimv2:Win32_LogonSession.LogonId="195361" != \\192.168.1.83\root\CIMV2:CIM_Process.Handle=7120
						lib_common.ErrorMessageHtml("Inconsistency:"+refMoniker + " != " + cgiMoniker )
					refInstanceUrl = lib_util.EntityUrlFromMoniker( refMoniker )
					refInstanceNode = lib_common.NodeUrl(refInstanceUrl)
					grph.add( ( wmiInstanceNode, lib_common.MakeProp(keyPrp), refInstanceNode ) )
			except AttributeError:
				# Then it is a literal attribute.
				# TODO: Maybe we could test if the type is an instance.
				# Beware: UnicodeEncodeError: 'ascii' codec can't encode character u'\\u2013'
				try:
					literalKeyValue[ keyPrp ] = str(valPrp)
				except UnicodeEncodeError:
					literalKeyValue[ keyPrp ] = "UnicodeEncodeError"


		# Now the literal properties are attached to the other node.
		if refInstanceNode != None:
			for keyLitt in literalKeyValue:
				grph.add( ( refInstanceNode, lib_common.MakeProp(keyLitt), lib_common.NodeLiteral( literalKeyValue[ keyLitt ] ) ) )

def Main():
	paramkeyDisplayNone = "Display none values"
	cgiEnv = lib_common.CgiEnv(can_process_remote=True,
									parameters = { paramkeyDisplayNone : "0" })

	displayNoneValues = cgiEnv.GetParameters( paramkeyDisplayNone ) in ( "1", "Y", "True")

	( nameSpace, className, entity_namespace_type ) = cgiEnv.GetNamespaceType()

	cimomUrl = cgiEnv.GetHost()

	sys.stderr.write("cimomUrl=%s ns=%s cls=%s id=%s\n" % ( cimomUrl, nameSpace, className, cgiEnv.m_entity_id) )

	grph = cgiEnv.GetGraph()

	try:
		connWmi = lib_wmi.WmiConnect(cimomUrl,nameSpace)
	except:
		exc = sys.exc_info()[1]
		lib_common.ErrorMessageHtml("Cannot connect to WMI server %s with namespace %s: %s" % ( cimomUrl,nameSpace, str(exc) ) )

	# Try to read the moniker, which is much faster,
	# but it does not always work if we do not have all the properties.
	cgiMoniker = cgiEnv.GetParameters("xid")
	sys.stderr.write("cgiMoniker=[%s]\n" % cgiMoniker )

	objList = WmiReadWithMoniker( cgiEnv, cgiMoniker )
	if objList is None:
		# If no object associated with the moniker, then tries a WQL query which might return several objects.
		objList = WmiReadWithQuery( cgiEnv, connWmi, className )

	wmiInstanceUrl = lib_util.EntityUrlFromMoniker( cgiMoniker )

	# Possible problem because this associates a single URL with possibly several objects ??
	wmiInstanceNode = lib_common.NodeUrl(wmiInstanceUrl)

	# This returns the map of units for all properties of a class.
	mapPropUnits = lib_wmi.WmiDictPropertiesUnit(connWmi, className)

	# We do not know what to do of the WQL query returns several WMI objects.
	for objWmi in objList:
		# sys.stderr.write("objWmi=[%s]\n" % str(objWmi) )

		# TODO: Attendre d'avoir plusieurs objects pour faire la meme chose que wentity_wbem,
		# c est a dire une deduplication adaptee avec creation d URL. Je me comprends.
		DispWmiProperties(grph,wmiInstanceNode,objWmi,displayNoneValues,className,mapPropUnits)

		# TODO: Pour ces classes, l'attente est tres longue. Rather create another link.
		# rchref = wmi.WMI().query("select * from Win32_UserAccount where Name='rchateau'")[0].references()
		# Several minutes for 139 elements.
		if not lib_wmi.WmiTooManyInstances( className ):
			try:
				DispWmiReferences(grph,wmiInstanceNode,objWmi,cgiMoniker)
			except:
				exc = sys.exc_info()[1]
				sys.stderr.write("Exception=%s\n" % str(exc) )
		else:
			# Prefixc with a dot so it is displayed first.
			grph.add( ( wmiInstanceNode, lib_common.MakeProp(".REFERENCES"), lib_common.NodeLiteral( "DISABLED" ) ) )

	# Adds the class node to the instance.
	wmiClassNode = lib_wmi.WmiAddClassNode(grph,connWmi,wmiInstanceNode, cimomUrl, nameSpace, className, lib_common.MakeProp(className) )

	# Now displays the base class, up to the top.
	lib_wmi.WmiAddBaseClasses(grph,connWmi,wmiClassNode,cimomUrl, nameSpace, className)

	# Now tries to find the equivalent object in the Survol terminology.
	AddSurvolObjectFromWmi(grph,wmiInstanceNode,connWmi,className,objList)

	# TODO: Embetant car il faut le faire pour toutes les classes.
	# Et en plus on perd le nom de la propriete.
	# cgiEnv.OutCgiRdf("LAYOUT_RECT",['root\\cimv2:CIM_Datafile'])
	# 'PartComponent' for 'root\\cimv2:CIM_Datafile'
	# 'Element' for 'root\\cimv2:Win32_DCOMApplication'
	# 'Antecedent' for 'CIM_DataFile'
	cgiEnv.OutCgiRdf("LAYOUT_TWOPI",[lib_common.MakeProp('PartComponent'),lib_common.MakeProp('Element'),lib_common.MakeProp('Antecedent')])
	# cgiEnv.OutCgiRdf("LAYOUT_SPLINE",[lib_common.MakeProp('PartComponent'),lib_common.MakeProp('Element'),lib_common.MakeProp('Antecedent')])

# TODO: Must add a link to our URL, entity.py etc...
# TODO: Must also add a link to associators.

if __name__ == '__main__':
	Main()
