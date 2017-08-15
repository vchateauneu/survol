import os
import re

mypath = "C:/tmp"
mypath = "C:/Users/rchateau/tmp"
mypath = "C:/Users/rchateau/AppData/Local/Temp"

print("Hello")


onlyfiles = []
for (dirpath, dirnames, filenames) in os.walk(mypath):
	onlyfiles.extend(filenames)
	break

print(onlyfiles)

def AnonymizeArr(splitFilnam):
	strForbidden = "*"

	# The file name extension is not taken into account.
	splitFilnam[-1] = strForbidden

	# ... no numbers:
	resu = [ strForbidden if tok.isdigit() else tok for tok in splitFilnam ]
	return resu

# TODO: PERFORMANCES:
# On peut plutot cluseriser en une seule passe en partant de la premiere version du code:
#         for wrd in lstWords:
#                 wrdSplit = re.split("[-\.0-9]+",wrd)
#
#                 lenWrds = len(wrdSplit)
#                 if lenWrds == 1:
#                         colsList = range( lenWrds )
#                 else:
#                         # There is also a specific index for the extension, if it exists,
#                         colsList = [-1]
#                         # The last element must go ONLY in the index labelled "-1".
#                         colsList.extend( range( lenWrds -1) )
#
#                 # The same word is indexed by each of its columns.
#                 for ixCol in colsList:
#                         try:
#                                 dictClusters = dictClustersArrays[ixCol]
#                         except KeyError:
#                                 # Add the missing element.
#                                 dictClustersArrays[ixCol] = {}
#                                 dictClusters = dictClustersArrays[ixCol]
#
#                         wrkKey = wrdSplit[ixCol]
#
#                         try:
#                                 dictClusters[wrkKey].append(wrd)
#                         except KeyError:
#                                 dictClusters[wrkKey] = [wrd]
#
# Quand on evalue chaque index, on peut voir s'il manque des objets
# car il n'avaient pas assez de token: On compte les objects indexes,
# et on fait la difference avec le nombre total.
# Cest plus rapide car une seule passe est necessaire, et moins de stockage.






# On tokenize et on essaye de rassembler
# les mots dont tous les tokens sont identiques, sauf un, puis sauf deux etc...
# en choisissant le minimum de tokens pour les plus grands clusters possibles.
# Et/Ou: Choisir un token, puis un autre.
# Plusieurs index, un par colonne: Ceux qui ont le token K a l;index N ?
#
# A la premiere passe, on choisit la colonne dont l'index est le plus petit
# mais avec au moins une clef (On peut peut-etre calculer l entropie).
#
# Selon le contexte, on pourrait traiter a part des most specifiques: i386, debug etc...
#
def all_clusts(lstWords):
	print(sorted(lstWords))

	dictSplits = {}

	maxCols = 0
	for wrd in lstWords:
		wrdSplit = re.split("[-\.0-9]+",wrd)

		lenWrds = len(wrdSplit)
		if maxCols < lenWrds:
			maxCols = lenWrds
		dictSplits[wrd] = wrdSplit

	# L'ajout de "-1" ne vaut que pour les noms de fichiers.
	allColsList = list( range( maxCols ) ) + [-1]
	print("")
	print("allColsList=%s"%str(allColsList))

	# One index, a dict, by column
	dictClustersArrays = { idxCol : dict() for idxCol in allColsList }

	for wrd in dictSplits:
		wrdSplit = dictSplits[wrd]

		lenWrds = len(wrdSplit)
		if lenWrds == 1:
			colsList = range( 1 )
			lastCol = 1
		else:
			# There is also a specific index for the extension, if it exists,
			# The last element must go ONLY in the index labelled "-1".
			colsList = list( range( lenWrds -1) ) + [-1]
			lastCol = lenWrds -1

		# The same word is indexed by each of its columns.
		for ixCol in colsList:
			dictClusters = dictClustersArrays[ixCol]

			wrkKey = wrdSplit[ixCol]

			try:
				dictClusters[wrkKey].append(wrd)
			except KeyError:
				dictClusters[wrkKey] = [wrd]

		# Missing columns are indexed with an empty string.
		for ixCol in range(lastCol,maxCols):
			dictClusters = dictClustersArrays[ixCol]
			wrkKey = ""
			try:
				dictClusters[wrkKey].append(wrd)
			except KeyError:
				dictClusters[wrkKey] = [wrd]


	for ixKey in dictClustersArrays:
		dictClusters = dictClustersArrays[ixKey]
		print("")
		print(ixKey)
		print(dictClusters)

	return dictClustersArrays


def cluster_maxsize(dictClusters):
	maxSz = 0
	for keyWrd in dictClusters:
		currSz = len(dictClusters[keyWrd])
		if maxSz < currSz:
			maxSz = currSz
	return maxSz

def clusterize_kol(lstWords):
	dictClustersArrays = all_clusts(lstWords)

	# Now choose the most selective index.
	# The goal might be to detect significant patterns (Entropy ?),
	# or simply to reduce the number of elements at each level, to facilite display.
	# Simple criteria: This chooses the index whose max category is the smallest.
	bestKey = None
	minMaxSz = 999999999
	for ixKey in dictClustersArrays:
		dictClusters = dictClustersArrays[ixKey]
		print("")
		print(ixKey)
		# print(dictClusters)
		currMax = cluster_maxsize(dictClusters)
		print("currMax=%d len=%d"%(currMax,len(dictClusters)))
		if currMax < minMaxSz:
			minMaxSz = currMax
			bestKey = ixKey

	print("bestKey=%s minMaxSz=%d"%(bestKey,minMaxSz))

	return dictClustersArrays[bestKey]



print("")
# clusterize(onlyfiles)
print("")
print("")
print("")
bstIdx = clusterize_kol(onlyfiles)
print("")
print("BEST")
print(bstIdx)