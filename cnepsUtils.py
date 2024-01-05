from pathlib import Path
import cneps
# def changeElement(inputList, target, newTarget):
#     for eachElem in inputList:

ctagsPath = cneps.ctagsPath
resPath = cneps.resPath
metaPath = cneps.metaPath
codeList = cneps.codeList
hdrList = cneps.hdrList
both = codeList + hdrList

def whoIsRoot(p1, p2):
    tmpP1 = Path(p1)
    tmpP2 = Path(p2)
    
    
    if tmpP2.is_relative_to(tmpP1) :
        # print("{} is child path of {}".format(tmpP1, tmpP2))
        return p1
    elif tmpP1.is_relative_to(tmpP2):
        # print("{} is child path of {}".format(tmpP2, tmpP1))
        return p2
    else:
        return False

def calcDist(filePath, hdrPaths, parsedHdr=None):
    origPath = "/".join(filePath.split("/")[:-1])
    ret = []
    # if(filePath == "clones/mongo/src/third_party/unwind/dist/src/ppc64/Ginit.c"):
    #     debug = True
    # else:
    #     debug = False
        
    curDist = 999999
    for eachHdr in hdrPaths:
        ### Least condition: header path should be included e.g., build/a.h -> build/ should be included
        if ( (parsedHdr != None) and (parsedHdr not in eachHdr) ):
            print("ERR???")
            print(parsedHdr)
            print(origPath)
            print(eachHdr)
            exit()

        ### calculate distance
        p1 = origPath.split("/")
        p2 = "/".join(eachHdr.split("/")[:-1])
        p2 = p2.split("/")
        totLen = len(p1) if len(p1) < len(p2) else len(p2)
        
        common = 0
        for i in range(1,totLen+2):
            if(p1[0:i] == p2[0:i]):
                # if (debug): 
                #     print(p1[0:i])
                #     print(p2[0:i])
                continue
            else:
                break
        common = i-1
        commonPath = p1[0:common]
        dist = len(p1) - common + len(p2) - common
        # if (debug): 
        #     print(eachHdr)
        #     print(len(p1), len(p2))
        #     print(len(p1) - common, len(p2) - common)
        #     print(common)
        #     print(commonPath)
        #     print(i, totLen+1)
        #     print(dist)

        if dist < curDist:
            ret = [eachHdr]
            curDist = dist 
        elif dist == curDist:
            ret.append(eachHdr)
            

    return ret

def calcDist2(hdrPath, filePaths, parsedHdr=None):
    origPath = "/".join(hdrPath.split("/")[:-1])
    ret = []
    curDist = 999999
    for eachFile in filePaths:
        ### Least condition: header path should be included e.g., build/a.h -> build/ should be included

        ### calculate distance
        p1 = origPath.split("/")
        p2 = "/".join(eachFile.split("/")[:-1])
        p2 = p2.split("/")
        totLen = len(p1) if len(p1) < len(p2) else len(p2)
        common = 0
        for i in range(1,totLen+1):
            if(p1[0:i] == p2[0:i]):
                # print(p1[0:i])
                # print(p2[0:i])
                continue
            else:
                break
        common = i-1
        commonPath = p1[0:common]
        dist = len(p1) - common + len(p2) - common

        if dist < curDist:
            ret = [eachFile]
            curDist = dist 
        elif dist == curDist:
            ret.append(eachFile)

    return ret

def makeHdrLookup(allNodes):
    hdr2path = {}
    path2node = {}
    for eachNode in allNodes:
        if eachNode == None:
            continue
        for eachHdrFile in eachNode.files:
            if eachHdrFile.endswith(both):
                
                hdrName = eachHdrFile.split("/")[-1]
                # pathOnly = "/".join(eachHdrFile.split("/")[:-1])

                if hdrName not in hdr2path:
                    hdr2path[hdrName] = []
                if eachHdrFile not in hdr2path[hdrName]:
                    hdr2path[hdrName].append(eachHdrFile)
                if eachHdrFile not in path2node:
                    path2node[eachHdrFile] = []
                path2node[eachHdrFile].append(eachNode)

    # nodes = []
    # for eachHdr in path2node:
    #     if(len(path2node[eachHdr])>1):
    #         print(eachHdr)
    #         print(path2node[eachHdr])
    #         for eachNode in path2node[eachHdr]:
    #             print(eachNode.OSS)
    #             print(eachNode)
    #         print()
        
    return hdr2path, path2node