"""
Azure cloud location
"""

import lib_common

def EntityOntology():
	return ( ["Subscription","Location"], )

def MakeUri(locaName, subscriptionName):
	return lib_common.gUriGen.UriMakeFromDict("Azure/location", { "Subscription" : subscriptionName, "Location" : locaName } )

