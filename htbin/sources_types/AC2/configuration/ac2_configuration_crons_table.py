#!/usr/bin/python

"""
Configuration Cron table
"""

import sys
import rdflib
import lib_common
import lib_util
import lib_uris
from sources_types.AC2 import configuration as AC2_configuration
from sources_types.AC2 import cronrules as AC2_cronrules
from sources_types.AC2 import trigger as AC2_trigger
from sources_types.AC2 import component as AC2_component

# <?xml version="1.0" encoding="utf-8" standalone="yes"?>
# <apps>
#    <crontable>
#        <cronrules cronid="AC2-App-Sample-A scheduling">
#            <trigger name="CRON#1"
#                     action="stop"
#                     force="true"
#                     components="A1"
#                     propagate="false"
#                     expression="0 00 * * * ? *"/>
#            <trigger name="CRON#3" action="stop" expression="0 30 * * * ? *"/>
#        </cronrules>
#    </crontable>
#     <hosts>
#         <host hostid="LOCAL"
#               host="127.0.0.1"
#               port="12567"/>
#     </hosts>
#     <app name="AC2-App-Sample-A"
#          version="Version-1"
#          notifref="AC2-App-Sample-A notification rule"
#          cronref="AC2-App-Sample-A scheduling">
def DisplayCronsTable(grph,configNode,configName):
	dom = AC2_configuration.GetDom(configName)

	# TODO: PROBLEME, ON DEVRAIT ALLER CHERCHER LES SOUS-NODES AU LIEU DE TOUT REPARCOURIR !!!!!!!!!!!
	for elt_apps in dom.getElementsByTagName('apps'):
		sys.stderr.write("Founds apps\n")

		DispCrons(dom,grph,configNode,configName)
		AC2_configuration.DispHosts(dom,grph,configNode)

propCronRules = lib_common.MakeProp("Cron rules")
propTrigger = lib_common.MakeProp("Trigger")
propComponents = lib_common.MakeProp("components")

def DispCrons(dom,grph,configNode,configName):
	for elt_crontable in dom.getElementsByTagName('crontable'):
		for elt_cronrules in elt_crontable.getElementsByTagName('cronrules'):
			attr_cronrules_cronid = elt_cronrules.getAttributeNode('cronid').value
			nodeCronrules = AC2_cronrules.MakeUri(configName,attr_cronrules_cronid)
			grph.add( ( configNode, propCronRules, nodeCronrules ) )

			for elt_trigger in elt_cronrules.getElementsByTagName('trigger'):
				attr_trigger_name = elt_trigger.getAttributeNode('name').value
				attr_trigger_name_no_sharp = attr_trigger_name.replace("CRON#","Cron ")
				nodeTrigger = AC2_trigger.MakeUri(configName,attr_cronrules_cronid,attr_trigger_name_no_sharp)

				# Many optional attributes.
				attr_trigger_action = elt_trigger.getAttributeNode('action')
				if attr_trigger_action:
					grph.add( ( nodeTrigger, lib_common.MakeProp("action"), rdflib.Literal( attr_trigger_action.value ) ) )

				attr_trigger_force = elt_trigger.getAttributeNode('force')
				if attr_trigger_force:
					grph.add( ( nodeTrigger, lib_common.MakeProp("force"), rdflib.Literal( attr_trigger_force.value ) ) )

				attr_trigger_components = elt_trigger.getAttributeNode('components')
				if attr_trigger_components:
					componentList = attr_trigger_components.value.split(",")
					for compNam in componentList:
						nodeComponent = AC2_component.MakeUri(configName,"hhhhhh",compNam)
						grph.add( ( nodeTrigger, propComponents, nodeComponent ) )

				attr_trigger_propagate = elt_trigger.getAttributeNode('propagate')
				if attr_trigger_propagate:
					grph.add( ( nodeTrigger, lib_common.MakeProp("propagate"), rdflib.Literal( attr_trigger_propagate.value ) ) )

				attr_trigger_expression = elt_trigger.getAttributeNode('expression')
				if attr_trigger_expression:
					grph.add( ( nodeTrigger, lib_common.MakeProp("expression"), rdflib.Literal( attr_trigger_expression.value ) ) )


				grph.add( ( nodeCronrules, propTrigger, nodeTrigger ) )


	return

def Main():

	cgiEnv = lib_common.CgiEnv()

	ac2File = cgiEnv.m_entity_id_dict["File"]

	sys.stderr.write("ac2File%s\n"% (ac2File) )

	grph = rdflib.Graph()

	configNode = AC2_configuration.MakeUri(ac2File)

	DisplayCronsTable(grph,configNode,ac2File)

	# cgiEnv.OutCgiRdf(grph, "LAYOUT_RECT", [pc.property_argument] )
	cgiEnv.OutCgiRdf(grph, "LAYOUT_RECT", [propTrigger,propComponents] )

if __name__ == '__main__':
	Main()

