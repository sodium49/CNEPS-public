import time
import os
import subprocess
import json
import cnepsPath

###
from cnepsUtils import *
ctagsPath = cnepsPath.ctagsPath
resPath = cnepsPath.resPath
metaPath = cnepsPath.metaPath
codeList = cnepsPath.codeList
hdrList = cnepsPath.hdrList
both = codeList + hdrList

class module():
    def __init__(self):
        self.OSS = "unknown"
        self.parent = []
        self.sub = []
        self.files = []
        self.root = ""    ## Which will become node's root
        self.center = ""

    def printModuleInfo(self):
        print("OSS Name: {}".format(self.OSS))
        print("Root of M: {}".format(len(self.root)))
        print("Parent Number: {}".format(len(self.parent)))
        print("Subs Number: {}".format(len(self.sub)))
        ### Sub into one Cat if the OSS exists, else make new one

def printAllModules(modules):
    for eachM in modules:
        print(eachM.OSS)
        print("CENTER: " + eachM.center)
        print("ROOT: " + eachM.root)
        print("\t Files:")
        for eachFile in eachM.files:
            print("\t\t" + eachFile)
        print()
        print("\t Subs:")
        for eachSub in eachM.sub:
            print("\t\t {}\t@\t{}".format(eachSub.OSS, eachSub.root))
        print()

def printModule(module, level=0):
    for eachM in module:
        print("\t"*level + eachM.OSS)
        print("\t"*level + "PATH: " + eachM.path)
        for eachFile in eachM.files:
            print("\t"*level + eachFile)
        print()
        if(eachM.sub):
            printModule(eachM.sub, level+1)

###################################################
def parseOSSinfo(targetPath, repoName):
    path2OSS = {}
    origOSSes = []  ## Debugging
    centrisResult = {} ## used for evaluation
    
    print("! 1-1 Reading CENTRIS result")

    stime = time.time()
    totOSS = 0

    with open(metaPath + "/" + repoName + "_centris" , "r") as fp:
        curOSS = ""
        ### Case OSS:
        for eachline in fp.readlines():
            if("OSS:" in eachline):
                curOSS = eachline.split("\n")[0].split("OSS: ")[1]
                totOSS += 1
                origOSSes.append(curOSS)
                if curOSS not in centrisResult:
                    centrisResult[curOSS] = []
                
            ### Case: functions
            else:
                eachLineSplitted = eachline.split("\t")

                for i in range(2, len(eachLineSplitted), 2):
                    funcName = eachLineSplitted[i+1].replace("\n", "")
                    filePath = targetPath + eachLineSplitted[i]
                    pathWithFunc = filePath + "\t" + funcName
                    if filePath not in centrisResult[curOSS]:
                        centrisResult[curOSS].append(filePath)
                        
                    if pathWithFunc not in path2OSS:
                        path2OSS[pathWithFunc] = []
                    path2OSS[pathWithFunc] += [curOSS]       
    
    ### END of parsing CENTRIS
    print("--- %s seconds ---" % (time.time() - stime))
    return path2OSS, centrisResult          
###################################################

def findHdr(hdrPaths, targetPath, targetFunc, path2proto):
    retHdr = []
    ### Find hdrs that contains myself as prototypes
    ### Least Condition: Need proto
    hdrCand = []
    for eachHdrPath in hdrPaths:
        if eachHdrPath not in path2proto:
            continue
        else:
            if targetFunc in path2proto[eachHdrPath]:
                hdrCand.append(eachHdrPath)
    retHdr = hdrCand
    return retHdr

                    # targetHdrPath = calcDist(eachFile, hdrPaths, parsedHdr=parsedHdr)
                    
def parseInclude(targetFile, targetFunc, hdr2path, path2proto, path2link):
    try:
        retCenter = []
        for parsedHdr in path2link[targetFile]:
            parsedHdrName = parsedHdr.split("/")[-1]

                # print(parsedHdr)
            if not parsedHdr.endswith(both):    ### High probability of external library call
                continue

            
            if parsedHdrName in hdr2path:  ### In case not in nodes list, we can't handle it
                hdrPaths = hdr2path[parsedHdrName]
                tmpPaths = []

                for eachHdrPaths in hdrPaths:
                    if parsedHdr in eachHdrPaths:
                        tmpPaths.append(eachHdrPaths)
                hdrPaths = tmpPaths

                if not hdrPaths:    ### System
                    continue
                ### Find hdrs that contains myself as prototypes
                targetHdrPath = findHdr(hdrPaths, targetFile, targetFunc, path2proto)

                # targetHdrPath = calcDist(eachFile, hdrPaths, parsedHdr=parsedHdr)
                if targetHdrPath: 
                    retCenter += targetHdrPath
    except: retCenter = []
    return retCenter

def parseDirs(targetFile, targetPath, targetFunc, hdr2path, path2proto):
    retCenter = []
    
    for eachFile in os.listdir(targetPath):
        # print(eachFile)
        filePath = os.path.join(targetPath, eachFile)
        if eachFile.endswith(hdrList):
            ### Check where function is defined
            if filePath not in path2proto:  ### File without prototypes should be passed
                continue 
            if targetFunc in path2proto[filePath]:
                retCenter.append(filePath)
                
    return retCenter

def moduleGen(targetPath, repoName, path2OSS):
    meta = {}
    path2proto = {}
    path2func = {}
    path2link  = {}
    
    moduleList = []
    # funcDict = {}
    path2mod = {}   ### Used for module lookup
    clsLinkedFuncs = {}

    hdr2path = {}

    
    ### Make meta data    
    if  os.path.exists(metaPath + "/" + repoName + "_meta.json"):
        with open(metaPath + "/" + repoName + "_meta.json", "r", encoding='utf-8', errors='ignore') as fp:
            meta = json.load(fp)
    else:   
        stime = time.time()
        print("! 2-1 Making function and prototype lookup table")
        for path, dir, files in os.walk(targetPath):
            for file in files:
                filePath = os.path.join(path, file)

                if file.endswith(both):
                    # path2func[filePath] = []
                    funcList = []
                    protoList = []
                    linkList = []
                # try:
                    ### Parse functions and prototypes
                    ### Ctag for func and proto
                    ctagsResult 		= subprocess.check_output(ctagsPath + ' -f - --output-format=json --kinds-C=fp --fields="*" "' + filePath + '"', stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')
                    for eachRec in ctagsResult.split("\n"):
                        if eachRec:
                            try:
                                eachRec = json.loads(eachRec)
                            except:
                                print("Ctag err")
                                print(eachRec)
                                continue
                            if eachRec["kind"] == "function":
                                funcName = eachRec["name"]
                                # path2func[filePath].append(funcName)
                                funcList.append(funcName)
                                
                            if eachRec["kind"] == "prototype" and file.endswith(hdrList):
                                protoName = eachRec["name"]
                                # protoList.append(protoName)
                                protoList.append(protoName)
                    
                    ### Parse imports
                    fp = open(filePath, "r", encoding="utf-8", errors="ignore")
                    fstring = fp.readlines()
                    for eachline in fstring:
                        ### Parse headers called module (or included in header file)
                        if  ("#include" in eachline) and \
                            (eachline.replace(" ", "")[0:len("#include")] == "#include"):
                            try:
                                parsedHdr = eachline.split("#include")[1].replace(" ", "")
                            except:
                                print("ERR!!")
                                print(filePath)
                                print(parsedHdr)
                                exit()
                            quote = parsedHdr[0]
                            quoteEnd = "\"" if quote=="\"" else ">"
                            parsedHdr = parsedHdr[1:]
                            parsedHdr = parsedHdr.split(quoteEnd)[0]
                            # parsedHdrName = parsedHdr.split("/")[-1]
                            linkList.append(parsedHdr)
            
                    if protoList:
                        # if filePath not in hdrDict:
                        path2proto[filePath] = protoList
                    if filePath in meta:
                        print("Meta parsing err")
                        exit()
                    meta[filePath] = {
                        "func": funcList,
                        "proto": protoList,
                        "link": linkList
                    }
        print("--- %s seconds ---" % (time.time() - stime))
    

        ## Write in json format
        # with open(metaPath + "/" + repoName + "_func.json", "w", encoding='utf-8', errors='ignore') as fp:
            # json.dump(path2func, fp)
        # with open(metaPath + "/" + repoName + "_proto.json", "w", encoding='utf-8', errors='ignore') as fp:
            # json.dump(path2proto, fp)
        with open(metaPath + "/" + repoName + "_meta.json", "w", encoding='utf-8', errors='ignore') as fp:
            json.dump(meta, fp)

            
    ### Meta to dict I need in this part
    for eachPath in meta:
        path2func[eachPath] = meta[eachPath]["func"]
        path2proto[eachPath] = meta[eachPath]["proto"]
        path2link[eachPath] = meta[eachPath]["link"]
    # path2func = meta["func"]
    # path2proto = meta["proto"]
    
    ### Make hdr lookup table first
    hdr2path = {}
    for eachPath in path2proto:
        hdrName = eachPath.split("/")[-1]
        if hdrName not in hdr2path: 
            hdr2path[hdrName] = []
        hdr2path[hdrName] += [eachPath]
        
        
    hdrLinkedFiles = {}
    ### Module constructoin
    if  not os.path.exists(metaPath + "/" + repoName + "_imports.json"):
        for path, dir, files in os.walk(targetPath):
            for file in files:
                if file.endswith(both):
                    filePath = os.path.join(path, file)
                    myfuncs = path2func[filePath]
                    if not myfuncs:
                        continue
                    
                    for eachFile in os.listdir(path):
                        if eachFile.endswith(hdrList):
                            eachHdr = os.path.join(path, eachFile)
                            # print(path2proto)
                            if eachHdr not in path2proto:
                                continue
                            protoList = path2proto[eachHdr]
                            s1 = [x.split("/")[-1] for x in protoList]
                            s2 = [x.split("/")[-1] for x in myfuncs]
                            common = list(set(s1).intersection(s2))
                            if (common):
                                if eachHdr not in hdrLinkedFiles:
                                    hdrLinkedFiles[eachHdr] = []
                                for eachCommonFuncs in common:
                                    eachPathNFuncs = filePath + "\t" + eachCommonFuncs
                                    if eachPathNFuncs not in hdrLinkedFiles[eachHdr]:
                                        hdrLinkedFiles[eachHdr].append(eachPathNFuncs)

    
    # print("! 2-2 Finding module centers")
    ### Generate simple module using header information
    stime = time.time()     
    # print(hdrDict)
    for eachPathWithFunc in path2OSS:
        eachFile, eachFunc = eachPathWithFunc.split("\t")
        eachPath = "/".join(eachFile.split("/")[:-1])
        

        """
        Module gen rules
        1. find included headers
        2. find in same dir (Same name has higher priority)mergin
        3. if both does not exists, new module is generated
        Duplicated? 
        """

        ### Rule 1 #include files
        centerCand = []
        centerCand += parseInclude(eachFile, eachFunc, hdr2path, path2proto, path2link)
        # print("INCLUDE PARSE RULE")
        
        ### Rule 2 files in same dir. Parse files in the same DIRS to find original function
        centerCand += parseDirs(eachFile, eachPath, eachFunc, hdr2path, path2proto)
        centerCand = list(set(centerCand)) ### Delete dup
        # print("DIR PARSE RULE")
        
        ### Rule 3 Nothing found as center candid, myself becomes module
        if not centerCand:
            centerCand = [eachFile]
            
        ### Miscs. used for lowering FPs 
        if eachFile in centerCand:
            centerCand = [eachFile]
        
        hdrVersion = eachFile.split("/")[-1]
        hdrVersion = ".".join(eachFile.split(".")[:-1])
        hdrVersions = [hdrVersion+".h", hdrVersion + ".hpp", hdrVersion+".hxx"]
        for eachCenterCand in centerCand:
            eachCenterCandName = eachCenterCand.split("/")[-1]
            for eachHdrVersion in hdrVersions:
                if eachHdrVersion == eachCenterCandName:
                    centerCand = [eachCenterCand]
                    break

        ### Debugging
        # centerCand = calcDist(targetPath, centerCand, parsedHdr=None)
        
        if len(centerCand) > 1:
            centerCand = calcDist(eachFile, centerCand)
            
        ### Link center with file + Func -> In canse multiple found
        for eachCenter in centerCand:
            fileNfunc = eachFile + "\t" + eachFunc
            if eachCenter not in clsLinkedFuncs:
                clsLinkedFuncs[eachCenter] = []
            if fileNfunc not in clsLinkedFuncs[eachCenter]:
                clsLinkedFuncs[eachCenter].append(fileNfunc)
                
                
    ### Check elements of segments
    """
    for eachHdr in hdrLinkedFiles:
        if not eachHdr in clsLinkedFuncs:
            continue ### SKIP segment that won't be used
        elemList = hdrLinkedFiles[eachHdr]
        file2paths = {}
        checkList = []
        newElemList = elemList

        ### Make Checklists
        for eachElem in elemList:
            fileName, funcName = eachElem.split("\t")
            fileNameOnly = fileName.split("/")[-1]
            if fileNameOnly not in file2paths:
                file2paths[fileNameOnly] = []
            if(fileName not in file2paths[fileNameOnly]):
                file2paths[fileNameOnly].append(fileName)
        print(hdrLinkedFiles[eachHdr])


        for eachFile in file2paths:
            if len(file2paths[eachFile]) ==1:
                continue
            ### DUPLICATED ELEMENT EXISTS!!!
            
            competeFiles = file2paths[eachFile]
            ret = calcDist2(eachHdr, competeFiles)
            print(competeFiles)
            print(ret)
            if(len(ret) == 1):
                ret = ret[0]
                competeFiles = competeFiles.pop(competeFiles.index(ret))
            else:
                print("XX")
                print(ret)
                continue ### Can not determine for this case
            # print(eachHdr)
            # print(competefiles)
            # print(ret)
            # print(competefiles.pop(competefiles.index(ret)))
            for eachElem in elemList:
                fileName, funcName = eachElem.split("\t")
                if (fileName in competeFiles):
                    newElemList.pop(newElemList.index(eachElem))
            # print(competefiles - ret)
        hdrLinkedFiles[eachHdr] = newElemList
        print(hdrLinkedFiles[eachHdr])
        
        # exit()
    """


    print("! 2-2 Module generation")
    for eachCenter in clsLinkedFuncs:
        newModule = module()
        
            
        linkedFiles = []
        func2file = {}
        ### Parse function and files included
        # print(clsLinkedFuncs[eachCenter])
        for eachFuncNFile in clsLinkedFuncs[eachCenter]:
            fileName, funcName = eachFuncNFile.split("\t")
            if fileName not in linkedFiles:
                linkedFiles.append(fileName)
            
                # print(eachFuncNFile, "\t", funcName)
            if funcName not in func2file:
                func2file[funcName] = []
            func2file[funcName] += [fileName]

        if eachCenter in hdrLinkedFiles:
            for eachFuncNFile in hdrLinkedFiles[eachCenter]:
                # for eachFuncNFile in funcNFilesList:
                fileName, funcName = eachFuncNFile.split("\t")
                if fileName not in linkedFiles:
                    linkedFiles.append(fileName)
            
                # print(eachFuncNFile, "\t", funcName)
                if funcName not in func2file:
                    func2file[funcName] = []
                func2file[funcName] += [fileName]

            
        # hdrOSS[eachHdr] = "unknown"
        newModule.OSS = "unknown"
        newModule.center = eachCenter
        centerRoot = os.path.commonpath(["/".join(eachCenter.split("/")[:-1])] + linkedFiles)

        # print()
        newModule.root = centerRoot
        newModule.files.append(eachCenter)
        # newModule.files += linkedFiles ### Add linked files
        ### Check OSS of paths
        
        ### Find main OSS and sub OSSes
        cnadidMainOSS = {}
        tmpOSS2Files = {}
        unknownFiles = []
        
        # Make PathNFuncs
        pathWithFuncList = []
        # /3rdParty/boost/1.78.0/libs/asio/example/cpp03/http/server3/request_parser.cpp	consume
        # /3rdParty/boost/1.78.0/libs/asio/example/cpp03/http/server3/request_parser.cpp	is_tspecial
           
        ctagsResult 		= subprocess.check_output(ctagsPath + ' -f - --output-format=json --kinds-C=fp --fields="*" "' + eachCenter + '"', stderr=subprocess.STDOUT, shell=True).decode(errors='ignore')
        protoList = []
        for eachRec in ctagsResult.split("\n"):
            if eachRec :
                try:
                    eachRec = json.loads(eachRec)
                except:
                    print("Ctag err")
                    print(eachRec)
                    continue
                ### Parse Prototypes
                if eachRec["kind"] == "prototype":
                    protoName = eachRec["name"]
                    protoList.append(protoName)
                    
                ### Parse functions
                if eachRec["kind"] == "function":
                    funcName = eachRec["name"]
                    pathWithFuncList.append(eachCenter + "\t" + funcName)
    
        ### find original functions for all prototypes
        # print(protoList)
        # print()
        for eachProto in protoList:
            # print(eachProto)
            if eachProto in func2file:  ### Already linked files list
                tmpFiles =  func2file[eachProto]
                for eachFile in tmpFiles:
                    pathWithFuncList.append(eachFile + "\t" + eachProto)
            ### Traverse to find same function in same dirs
            ### THIS will not impact a lot since we already included all files with OSSes => PASS
            # else:
            #     hdrDir = "/".join(eachCenter.split("/")[:-1])
            #     for eachFile in os.listdir(hdrDir):
            #         print(eachProto)
            #         print(hdrDir + "/" + eachFile)

        for pathNFunc in pathWithFuncList:
            if pathNFunc in path2OSS:
                tmpOSSes = path2OSS[pathNFunc]

                for eachTmpOSS in tmpOSSes:
                    ### Make temporary lookup table for making sub-component module
                    tmpPath = pathNFunc.split("\t")[0]
                    if(eachTmpOSS not in tmpOSS2Files):
                        tmpOSS2Files[eachTmpOSS] = []
                    if(eachTmpOSS not in tmpOSS2Files[eachTmpOSS]):
                        tmpOSS2Files[eachTmpOSS].append(tmpPath)
                    ### End of making lookup table
                    
                    if(eachTmpOSS not in cnadidMainOSS):
                        cnadidMainOSS[eachTmpOSS] = 0
                    cnadidMainOSS[eachTmpOSS] +=1
            else:
                tmpPath = pathNFunc.split("\t")[0]
                if tmpPath not in unknownFiles:
                    unknownFiles.append(tmpPath)
            
        ### Check highest proportion of OSS to find main OSS
        if cnadidMainOSS:
            mainOSS = max(cnadidMainOSS, key=cnadidMainOSS.get)
            newModule.OSS = mainOSS
            ### regard unknown files as main module
            newModule.files += unknownFiles

            if eachCenter not in path2mod:
                path2mod[eachCenter] = []
            # else:
            #     print(3)
            #     print(path2mod[eachHdr])
            path2mod[eachCenter] += [newModule]
            
            ### Generate file to module lookup table
            ### add files to module
            ### generate sub module

            for eachOSS in cnadidMainOSS:
                ### Add files related to main OSS into main module
                if eachOSS == mainOSS:

                    # newModule.files += tmpOSS2Files[eachOSS]
                    for eachFile in tmpOSS2Files[eachOSS]:
                        if eachFile not in newModule.files:
                            newModule.files.append(eachFile)
                        if(eachFile not in path2mod):
                            path2mod[eachFile] = []
                        # else:
                        #     print(3)
                        #     print(path2mod[eachFile])
                        path2mod[eachFile] += [newModule]  #This may cause duplicated module assigning
                
                ### Generate sub module
                else:
                # print(eachOSS, mainOSS)
                    newSubModule = module()
                    newSubModule.OSS = eachOSS
                    newSubModule.center = eachCenter
                    newSubModule.root = centerRoot
                    ### Make link to each other
                    newModule.sub.append(newSubModule)
                    newSubModule.parent.append(newModule)
                    newSubModule.files += tmpOSS2Files[eachOSS]
                    for eachFile in tmpOSS2Files[eachOSS]:
                        if(eachFile not in path2mod):
                            path2mod[eachFile] = []
                        # else:
                        #     print(3)
                        #     print(path2mod[eachFile])
                        path2mod[eachFile] += [newModule]
                    newSubModule.files = list(set(newSubModule.files))
                    moduleList.append(newSubModule)


            # hdrOSS[eachHdr] = mainOSS
            newModule.files = list(set(newModule.files)) ### delete dups
            moduleList.append(newModule)

    
    print("--- %s seconds ---" % (time.time() - stime))
    
    
    ## Update hdr2path to include ALL FILES
    for eachPath in path2func:
        hdrName = eachPath.split("/")[-1]
        if hdrName not in hdr2path:
            hdr2path[hdrName] = []
        if eachPath not in hdr2path[hdrName]:
            hdr2path[hdrName] += [eachPath]

    return moduleList, path2mod, hdr2path, meta

def test():
    repoPath = "clones/mongo"
    repoName = "mongo"
    path2OSS, centrisResult = parseOSSinfo(repoPath, repoName)
    module, path2mod, hdr2path = moduleGen(repoPath, repoName, path2OSS)
    print(module)
    
    for eachM in module:
        # print(eachM)
        print(eachM)
        print(eachM.OSS)
        print("\t" + str(eachM.files))
        print("\t" + eachM.root)
        print()
        if eachM.sub:
            print("sub: ")
            for eachSub in eachM.sub:
                print("\t" + eachSub.OSS)
                print("\t\t" + eachSub.root)
                print("\t\t" + str(eachSub.files))
                print()
                
    print("Total module found: {}\n".format(len(module)))
    OSSes = []
    for eachM in module:
        if eachM.OSS not in OSSes:
            OSSes.append(eachM.OSS)
    print(OSSes)
    print("Total OSS after module gen: {}\n".format(len(OSSes)))
    print()
    print("No dup? {}".format( len(module) == len(set(module))))

    

if __name__=="__main__":
    test()