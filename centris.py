
"""
OSS List Detector.
Author:		Seunghoon Woo (seunghoonwoo@korea.ac.kr)
Modified: 	December 16, 2020.

Modified by:	Anonymous
Modified: 		November. 17, 2023.
"""

import os
import sys
import re
import shutil
import json
import tlsh
import subprocess

import cnepsPath

"""GLOBALS"""
currentPath		= os.getcwd()
theta			= 0.1
# resultPath		= currentPath + "/meta_dejavue/"
resultPath		= cnepsPath.metaPath
finalDBPath		= currentPath + "/componentDB/"
aveFuncPath		= currentPath + "/metaInfos/aveFuncs"
ctagsPath		= currentPath + "/bin/ctags"

# shouldMake 	= [resultPath]
# for eachRepo in shouldMake:
# 	if not os.path.isdir(eachRepo):
# 		os.mkdir(eachRepo)

# Generate TLSH
def computeTlsh(string):
	string 	= str.encode(string)
	hs 		= tlsh.forcehash(string)
	return hs


def removeComment(string):
	# Code for removing C/C++ style comments. (Imported from VUDDY and ReDeBug.)
	# ref: https://github.com/squizz617/vuddy
	c_regex = re.compile(
		r'(?P<comment>//.*?$|[{}]+)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
		re.DOTALL | re.MULTILINE)
	return ''.join([c.group('noncomment') for c in c_regex.finditer(string) if c.group('noncomment')])

def normalize(string):
	# Code for normalizing the input string.
	# LF and TAB literals, curly braces, and spaces are removed,
	# and all characters are lowercased.
	# ref: https://github.com/squizz617/vuddy
	return ''.join(string.replace('\n', '').replace('\r', '').replace('\t', '').replace('{', '').replace('}', '').split(' ')).lower()

def hashing(repoPath):
	# This function is for hashing C/C++ functions
	# Only consider ".c", ".cc", and ".cpp" files
	possible = (".c", ".cc", ".cpp")
	
	fileCnt  = 0
	funcCnt  = 0
	lineCnt  = 0

	resDict  = {}

	for path, dir, files in os.walk(repoPath):
		for file in files:
			filePath = os.path.join(path, file)

			if file.endswith(possible):
				try:
					# Execute Ctgas command

					###/home/noory/workfolder/sbom/ctree/centris/DBprocessing/../../impl/bin/ctags -f - --kinds-C="*"" --fields=neKSt "../../impl/mongo/src/mongo/scripting/mozjs/maxkey.cpp"
					functionList 	= subprocess.check_output(ctagsPath + ' -f - --kinds-C=* --fields=neKSt "' + filePath + '"', stderr=subprocess.STDOUT, shell=True).decode(errors="ignore")

					f = open(filePath, 'r', encoding = "UTF-8", errors='ignore')

					# For parsing functions
					lines 		= f.readlines()
					allFuncs 	= str(functionList).split('\n')
					func   		= re.compile(r'(function)')

					number 		= re.compile(r'(\d+)')
					funcSearch	= re.compile(r'{([\S\s]*)}')
					tmpString	= ""
					funcBody	= ""

					fileCnt 	+= 1

					for i in allFuncs:
						elemList	= re.sub(r'[\t\s ]{2,}', '', i)
						elemList 	= elemList.split('\t')
						funcBody 	= ""

						if i != '' and len(elemList) >= 8 and func.fullmatch(elemList[3]):
							funcName 		 = elemList[0]
							# print(elemList)
							funcStartLine 	 = int(number.search(elemList[4]).group(0))
							funcEndLine 	 = int(number.search(elemList[7]).group(0))

							tmpString	= ""
							tmpString	= tmpString.join(lines[funcStartLine - 1 : funcEndLine])

							if funcSearch.search(tmpString):
								funcBody = funcBody + funcSearch.search(tmpString).group(1)
							else:
								funcBody = " "

							funcBody = removeComment(funcBody)
							funcBody = normalize(funcBody)
							funcHash = computeTlsh(funcBody)

							if len(funcHash) == 72 and funcHash.startswith("T1"):
								funcHash = funcHash[2:]
							elif funcHash == "TNULL" or funcHash == "" or funcHash == "NULL":
								continue

							storedPath = filePath.replace(repoPath, "", 1)
							if funcHash not in resDict:
								resDict[funcHash] = []
							resDict[funcHash].append(storedPath + "\t" + funcName)

							lineCnt += len(lines)
							funcCnt += 1

				except subprocess.CalledProcessError as e:
					print("Parser Error:", e)
					continue
				except Exception as e:
					print ("Subprocess failed", e)
					continue

	return resDict, fileCnt, funcCnt, lineCnt 

def getAveFuncs():
	aveFuncs = {}
	with open(aveFuncPath, 'r', encoding = "UTF-8", errors='ignore') as fp:
		aveFuncs = json.load(fp)
	return aveFuncs

def readComponentDB():
	componentDB = {}
	jsonLst 	= []

	for OSS in os.listdir(finalDBPath):
		componentDB[OSS] = []
		with open(finalDBPath + OSS, 'r', encoding = "UTF-8", errors='ignore') as fp:
			jsonLst = json.load(fp)
			for eachHash in jsonLst:
				hashval = eachHash["hash"]
				vers = eachHash["vers"]
				componentDB[OSS].append(hashval)
	return componentDB

def detector(inputDict, inputRepo, componentDB):
	fres		= open(resultPath + "/" + inputRepo + "_centris", 'w')
	aveFuncs 	= getAveFuncs()
	cnt = 0
	for OSS in componentDB:
		commonFunc 	= []
		repoName 	= OSS.split('_sig')[0]
		totOSSFuncs = float(aveFuncs[repoName])
		if totOSSFuncs == 0.0:
			continue
		comOSSFuncs = 0.0
		for hashval in componentDB[OSS]:
			if hashval in inputDict:
				commonFunc.append(hashval)
				comOSSFuncs += 1.0		

		if (comOSSFuncs/totOSSFuncs) >= theta:
			fres.write("OSS: " + OSS + '\n')

			# If you want to see the detail path information,
			# please uncomment the below codes
			
			for hashFunction in commonFunc:
				# print(inputDict[hashFunction])
				fres.write('\t' + hashFunction + "\t" + "\t".join(inputDict[hashFunction]) +  '\n')

	fres.close()


def main(inputPath, inputRepo, testmode=0):
	componentDB = readComponentDB()
	if testmode == 1:
		inputDict = {}
		with open(inputPath, 'r', encoding = "UTF-8", errors="ignore") as fp:
			body = ''.join(fp.readlines()).strip()
			for eachLine in body.split('\n')[1:]:
				hashVal = eachLine.split('\t')[0]
				hashPat = eachLine.split('\t')[1]
				inputDict[hashVal] = hashPat
	else:
		inputDict, fileCnt, funcCnt, lineCnt = hashing(inputPath)

	detector(inputDict, inputRepo, componentDB)


""" EXECUTE """
if __name__ == "__main__":
	

	testmode = 0

	if testmode:
		inputPath = currentPath + "/fuzzy_arangodb(v3.5.0).hidx"
		inputRepo = "arangodb"
	else:
		inputPath = sys.argv[1]
		inputRepo = inputPath.split('/')[-1]

	main(inputPath, inputRepo, testmode)