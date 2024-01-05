#!/usr/bin/python3
### default lib
import sys
import os
import time

### Implementation
import centris
import cnepsPath
from cnepsGraph import *
from cnepsModule import *
from cnepsUtils import * 



ctagsPath = cnepsPath.ctagsPath
resPath = cnepsPath.resPath
metaPath = cnepsPath.metaPath
codeList = cnepsPath.codeList
hdrList = cnepsPath.hdrList
both = codeList + hdrList
## Run command: python3 implementation.py clones/mongo



def parseRepoName(inputPath):
    repoName = inputPath
    if(inputPath[-1] == "/"):
        ### DELETE / at the end
        inputPath = inputPath[:-1]

    if(inputPath[0:2] == "./"):
        repoName = inputPath[2:]
    repoName = repoName.split("/")[-1]
    return repoName

def genNodes(modules):
    allNodes = []
    edges = {}
    # path2nodes = {}

    ### Make nodes for each modules and combine same nodes in same path
    print("! 3-1 make nodes for each module, components")
    for eachM in modules:
        if eachM.parent:
            continue
        # root = "/".join(eachM.root.split("/")[:-1])
        root = eachM.root
        flag = False
        ### Check for same nodes in target path
        newNode = gnode()
        newNode.OSS = eachM.OSS
        newNode.root = root
        newNode.files = []
        newNode.insM(eachM, allNodes, edges)
        allNodes.append(newNode)
        
    ### Inspect nodes
    for eachNode in allNodes:
        for eachChild in eachNode.child:
            if eachNode not in eachChild.parent:
                print ("-_-")
                exit()
        for eachParent in eachNode.parent:
            if(eachNode not in eachParent.child):
                print(" -_---")
                exit()

    return allNodes, edges

def linkedReuseAnalysis(repoName, allNodes, hdr2path, meta, edges):
    # print(edges)
    ### Generate header directory lookup table
    depsResult = []
    FNmonitor = {}
    path2func = {}
    path2proto = {}
    path2link = {}
    NOTUSED_hdr2path, path2node = makeHdrLookup(allNodes)
    
    ## Meta parser
    for eachPath in meta:
        path2func[eachPath] = meta[eachPath]["func"]
        path2proto[eachPath] = meta[eachPath]["proto"]
        path2link[eachPath] = meta[eachPath]["link"]


    print("! 4-1 Analyzing Links in Other Nodes...")
    # print("Num nodes before deps analysis:{}".format(len(allNodes)))
    for eachNode in allNodes:
        if not eachNode:   ### In case deleted nodes such as merge action
            continue
        ### Analyze files to find if this node has link to other node
        for eachFile in eachNode.files:
            # fp = open(eachFile, "r", encoding="utf-8", errors="ignore")
            # fstring = fp.readlines()
            
            ### Get imports
            parsedHdrList = path2link[eachFile]
            for parsedHdr in parsedHdrList:
                parsedHdrName = parsedHdr.split("/")[-1]
                # print(parsedHdr)
                if not parsedHdr.endswith(both):
                    continue
                if parsedHdrName in hdr2path:  ### In case not in nodes list, we can't handle it
                    hdrPaths = hdr2path[parsedHdrName]
                    tmpPaths = []
                    for eachHdrPaths in hdrPaths:
                        if parsedHdr in eachHdrPaths:
                            tmpPaths.append(eachHdrPaths)
                    hdrPaths = tmpPaths
                    if not hdrPaths:    ### System Libs
                        continue

                    targetHdrPaths = calcDist(eachFile, hdrPaths, parsedHdr=parsedHdr)
                    if len(targetHdrPaths) > 1:
                        # print("ERR T_T")
                        # print(targetHdrPaths)
                        # print(eachFile)
                        # print(hdrPaths)
                        if eachNode not in FNmonitor:
                            FNmonitor[eachNode] = []
                        toAdd = eachFile + " => "
                        for eachTargetHdrPath in targetHdrPaths:
                            toAdd += "\n\t\t" + eachTargetHdrPath

                        FNmonitor[eachNode].append(toAdd)
                        FNmonitor[eachNode] = list(set(FNmonitor[eachNode]))
                        continue    ### Can not determine for this case...
                    
                    ### When only one candidates left, we can determine with first index
                    targetHdrPath = targetHdrPaths[0]
                    if not targetHdrPaths:
                        # print("ERR")
                        # exit()
                        if eachNode not in FNmonitor:
                            FNmonitor[eachNode] = []
                        toAdd = eachFile + " -> " + parsedHdr
                        FNmonitor[eachNode].append(toAdd)
                        FNmonitor[eachNode] = list(set(FNmonitor[eachNode]))
                        continue ### Nothing to resolve may introduce FNs, monitor it

                    for eachTargetHdrPath in targetHdrPaths:
                        targetHdrPath = eachTargetHdrPath

                        if targetHdrPath in path2node:
                            # print(targetHdrPath)

                            targetNodeList = path2node[targetHdrPath]

                            for targetNode in targetNodeList:

                            # print(path2m[target].OSS)
                                if targetNode == eachNode:
                                    continue
                                
                                ### Same OSS -> Same node // If same name, different path file exists, not a case
                                f1 = [x.split("/")[-1] for x in targetNode.files]
                                f2 = [x.split("/")[-1] for x in eachNode.files]
                                common = list(set(f1).intersection(f2))
                                
                                if targetNode.OSS != eachNode.OSS:
                                    depsResult.append("OSS {} -> {} DIFF \n {} -> {}".format(eachNode.OSS, targetNode.OSS, eachFile, targetHdrPath))
                                    depsStr = "\tOSS {} -> {} IMPORT \n\t{} -> {}\n".format(eachNode.OSS, targetNode.OSS, eachFile, targetHdrPath)

                                    ### Incase already inside, pass
                                    if targetNode in eachNode.child:
                                        continue
                                    eachNode.child.append(targetNode)
                                    eachNode.deps.append(depsStr)
                                    eachNode.deps = list(set(eachNode.deps))
                                    targetNode.parent.append(eachNode)
                                    newEdge = "{} -> {}".format(eachNode, targetNode)
                                    if newEdge not in edges:
                                        edges[newEdge] = "link"
                                    elif edges[newEdge] == "inc":
                                        edges[newEdge] += "\tlink"

                else:
                    continue

    allNodes = clearNodeList(allNodes)
    
    # ### For verification
    # with open(metaPath + "/" + repoName + "_deps.txt", "w", encoding='utf-8', errors='ignore') as fp:
        
    #     ### Generate Human Readable reseult
    #     for eachRes in depsResult:

    #         fp.write(eachRes + "\n\n")

    return allNodes, edges, FNmonitor


def mergeSameDirNodes(allNodes, edges, FNmonitor, meta):
    oss2nodes = {}
    
    ### Make path-node lookup table
    for eachNode in allNodes:
        OSS = eachNode.OSS
        if OSS not in oss2nodes: 
            oss2nodes[OSS] = []
        if eachNode not in oss2nodes[OSS]: 
            oss2nodes[OSS].append(eachNode)
    print("Nodes before merging same dir nodes: ",len(allNodes))
    ### Merge nodes in same root and same OSS
    for eachOSS in oss2nodes:
        
        # print(eachOSS)
        roots = []
        root2node = {}
        nodes = oss2nodes[eachOSS]
        # print(nodes)
        ### Collect all nodes
        for targetNode in nodes:
            targetRoot = targetNode.root
            
            ### Empty roots, for first iteration
            if not roots:
                # print("New Root!: ", targetRoot)
                roots.append(targetRoot)
                root2node[targetRoot] = targetNode
                continue
            newRoot = True
            for eachRoot in roots:
                
                parentRoot = whoIsRoot(eachRoot, targetRoot)
                
                if parentRoot:
                    newRoot = False
                    ### parent node is originally existing roots
                    if parentRoot == eachRoot:
                        parentNode = root2node[eachRoot]
                        childNode = targetNode
                    else:
                        parentNode = targetNode
                        childNode = root2node[eachRoot]
                        ### Update with new roots
                        roots[roots.index(eachRoot)] = targetRoot
                        roots = list(set(roots))
                        del root2node[eachRoot]
                        root2node[targetRoot] = targetNode
                    # print("Merge into...: ", parentNode, targetNode)
                    
                    mergeNode(parentNode, childNode, allNodes)
                    ### FN monitor update
                    if childNode in FNmonitor:
                        toAdd = FNmonitor[childNode]
                        if parentNode not in FNmonitor:
                            FNmonitor[parentNode] = []
                        FNmonitor[parentNode] += toAdd
                        FNmonitor[parentNode] = list(set(FNmonitor[parentNode]))
                    ### Update edges information
                    edges = updateEdges(parentNode, childNode, edges)
                    if childNode ==targetNode:
                        break
            if newRoot:
                root2node[targetRoot] = targetNode
                roots.append(targetRoot)
        print(eachOSS)
        for eachRoot in roots:
            print(eachRoot)
        print()
    allNodes = clearNodeList(allNodes) ### Cleanse allnodes

    # print(sum)
    print("Nodes after merging same dir nodes: ",len(allNodes))

    # print(allNodes)
    rootNodes = []
    for eachNode in allNodes:
        # print(eachNode)
        if eachNode.parent:
            # print(eachNode)
            # print(eachNode.parent)
            continue
        rootNodes.append(eachNode)
    # print("--- %s seconds ---" % (time.time() - stime))
    return rootNodes, allNodes, edges, FNmonitor
    
def originCandidGen(allNodes):
    for eachNode in allNodes:
        ### If none in origin, it's linked reused one
        # if [None] == eachNode.src:
            
        ### Compare path of nodes
        for eachParent in eachNode.parent:
            # eachParent.root
            parentRoot = Path(eachParent.root)
            myRoot = Path(eachNode.root)
            # print(parentRoot)
            # print(myRoot)
            # print()
            if myRoot.is_relative_to(parentRoot) :
                # if ( myRoot != parentRoot):
                    # print(myRoot, parentRoot)
                # exit()
                eachNode.src.append(eachParent)
        if len(eachNode.src) > 1:
            # print(555)
            # print(eachNode.src)
            eachNode.src = list(set(eachNode.src))
            # print(eachNode.src)
            if None in eachNode.src:
                eachNode.src.pop(eachNode.src.index(None))
            # print(eachNode.src)
    return allNodes


def checkLinkExists(eachNode, checkNode, allNodes, hdr2path, meta):
    
    ### Generate header directory lookup table
    depsResult = []
    FNmonitor = {}
    path2func = {}
    path2proto = {}
    path2link = {}
    NOTUSED_hdr2path, path2node = makeHdrLookup(allNodes)

    ## Meta parser
    for eachPath in meta:
        path2func[eachPath] = meta[eachPath]["func"]
        path2proto[eachPath] = meta[eachPath]["proto"]
        path2link[eachPath] = meta[eachPath]["link"]
        
    for eachFile in eachNode.files:
        # fp = open(eachFile, "r", encoding="utf-8", errors="ignore")
        # fstring = fp.readlines()
        
        ### Get imports
        parsedHdrList = path2link[eachFile]

        for parsedHdr in parsedHdrList:
            parsedHdrName = parsedHdr.split("/")[-1]
            # print(parsedHdr)
            if not parsedHdr.endswith(both):
                continue
            if parsedHdrName in hdr2path:  ### In case not in nodes list, we can't handle it
                hdrPaths = hdr2path[parsedHdrName]
                tmpPaths = []
                for eachHdrPaths in hdrPaths:
                    if parsedHdr in eachHdrPaths:
                        tmpPaths.append(eachHdrPaths)
                hdrPaths = tmpPaths
                if not hdrPaths:    ### System Libs
                    continue

                targetHdrPaths = calcDist(eachFile, hdrPaths, parsedHdr=parsedHdr)
                if len(targetHdrPaths) > 1:

                    if eachNode not in FNmonitor:
                        FNmonitor[eachNode] = []
                    toAdd = eachFile + " => "
                    for eachTargetHdrPath in targetHdrPaths:
                        toAdd += "\n\t\t" + eachTargetHdrPath

                    FNmonitor[eachNode].append(toAdd)
                    FNmonitor[eachNode] = list(set(FNmonitor[eachNode]))
                    continue    ### Can not determine for this case...
                
                ### When only one candidates left, we can determine with first index
                targetHdrPath = targetHdrPaths[0]
                if not targetHdrPaths:
                    # print("ERR")
                    # exit()
                    if eachNode not in FNmonitor:
                        FNmonitor[eachNode] = []
                    toAdd = eachFile + " -> " + parsedHdr
                    FNmonitor[eachNode].append(toAdd)
                    FNmonitor[eachNode] = list(set(FNmonitor[eachNode]))
                    continue ### Nothing to resolve may introduce FNs, monitor it

                for eachTargetHdrPath in targetHdrPaths:
                    targetHdrPath = eachTargetHdrPath
                    
                    if targetHdrPath in path2node:
                        targetNodeList = path2node[targetHdrPath]

                        for targetNode in targetNodeList:
                        # print(path2m[target].OSS)
                            if targetNode == eachNode:
                                continue
                            if targetNode == checkNode:
                                return True, eachFile, targetHdrPath
    return False, None, None

def mergeSameSrcNodes(allNodes, edges, FNmonitor, hdr2path, meta):
    path2func = {}
    path2proto = {}
    path2link = {}
    oss2nodes = {}
    
    ## Meta parser
    for eachPath in meta:
        path2func[eachPath] = meta[eachPath]["func"]
        path2proto[eachPath] = meta[eachPath]["proto"]
        path2link[eachPath] = meta[eachPath]["link"]
        
    ### Make path-node lookup table
    
    checkedNodes = []
    ## collecting nodes with same OSS for easy merging
    for eachNode in allNodes:
        OSS = eachNode.OSS
        if OSS not in oss2nodes: 
            oss2nodes[OSS] = []
        if eachNode not in oss2nodes[OSS]: 
            oss2nodes[OSS].append(eachNode)
            

    ### variable setup for O(n^2) comparison, this is needed because list of nodes changes frequently
    i = 0
    EOL_out = len(allNodes)
    ### Iterates all nodes to find nodes from same sources
    for eachNode in allNodes:

        if eachNode == None:
            continue
        
        ### Gather nodes with same OSS
        # targetNodesList = oss2nodes[eachNode.OSS]
        
        ### Comparing target node selection
        # for targetNode in allNodes:
        j = 0
        EOL_in = len(allNodes)
        # while EOL_in:
            # if j == EOL_in:
                # EOL_in = False
                # continue
        for targetNode in allNodes:
            # targetNode = allNodes[j]
            # j += 1
            ### Since we are using the same list, targetnode can be same, at that case, skip it
            if eachNode == targetNode or \
                targetNode == None or \
                targetNode.OSS != eachNode.OSS:
                continue
            ### DEbug Codes
            # print(eachNode.OSS)
            # print(eachNode.root)
            # print(targetNode.root)
            
            # print("myNodeSrc")
            # print(eachNode.src)
            # for eachSrc in eachNode.src:
            #     if(eachSrc):
            #         print("\t" + eachSrc.OSS)
            #         print("\t" + eachSrc.root)
                
            # print("targetNodeSrc")
            # print(targetNode.src)
            # for eachSrc in targetNode.src:
            #     if(eachSrc):
            #         print("\t" + eachSrc.OSS)
            #         print("\t" + eachSrc.root)
            # print()
            ### DEbug Codes
            mergeFlag = False
            # checkedNodes.append(eachNode)

            ## Must condition => First condition: No duplicated files inside
            f1 = [x.split("/")[-1] for x in eachNode.files]
            f2 = [x.split("/")[-1] for x in targetNode.files]
            commonFile = list(set(f1).intersection(f2))
            # if common : ### Duplicate found -> skip
            #     print("common files...")
            #     continue
            
            ### Compare roots
            r1 = eachNode.root
            r2 = targetNode.root
            newRoot = os.path.commonpath([eachNode.root, targetNode.root])
            parentRoot = whoIsRoot(r1, r2)


            commonSrc = list(set(eachNode.src).intersection(targetNode.src))
            linkExists, eachFile, targetHdrPath = checkLinkExists(eachNode, targetNode, allNodes, hdr2path, meta)

            ### Reuse between two components
            if linkExists and commonFile:
                # depsResult.append("OSS {} -> {} DIFF \n {} -> {}".format(eachNode.OSS, targetNode.OSS, eachFile, targetHdrPath))
                depsStr = "\tOSS {} -> {} IMPORT \n\t{} -> {}\n".format(eachNode.OSS, targetNode.OSS, eachFile, targetHdrPath)

                ### Incase already inside, pass
                if targetNode in eachNode.child:
                    continue
                eachNode.child.append(targetNode)
                eachNode.deps.append(depsStr)
                eachNode.deps = list(set(eachNode.deps))
                targetNode.parent.append(eachNode)
                # targetNode.deps.append(depsStr)
                # targetNode.deps = list(set(eachNode.deps))
                ### Update edges information
                newEdge = "{} -> {}".format(eachNode, targetNode)
                # print(newEdge)
                # edgeStr = "{} -> {}".format(self, newSubNode)
                
                # if newEdge in edges:
                    # print(99979)
                    # print(newEdge)
                    # print(edges[newEdge])
                if newEdge not in edges:
                    # print(555657)
                    edges[newEdge] = "link"
                elif edges[newEdge] == "inc":
                    # print(444)
                    edges[newEdge] += "\tlink"
            ### Cond 1 - Common Source Found
            if commonSrc or parentRoot or (linkExists and not commonFile):
            # if parentRoot != None and eachNode.src.OSS == targetNode.src.OSS:
                ### Set merge flag for avoiding duplicated merging on second condition - parent comparison
                mergeFlag = True
                ### Set
                # if parentRoot == r1:
                parentNode = eachNode
                childNode = targetNode
                # else:
                #     parentNode = targetNode
                #     childNode = eachNode
            
            if mergeFlag:
                ### Update by deleting merged node
                
                ### If source is changed, the node should be rechecked
                for eachRelatedNode in list(set(parentNode.child + parentNode.parent +  childNode.child + childNode.parent)) :
                    if eachRelatedNode.src == childNode or eachRelatedNode.src == parentNode:
                        # if eachRelatedNode in allNodes:
                        if (eachRelatedNode == childNode):
                            print("THIS!")
                            exit()
                        allNodes[allNodes.index(eachRelatedNode)] = None
                        # allNodes[allNodes.index(n2)] = None
                        allNodes.append(eachRelatedNode)
                        EOL_in += 1  ### 
                        EOL_out += 1 
                    
                ###
                mergeNode(parentNode, childNode, allNodes, newRoot=newRoot)

                
                ### FN monitor update
                if childNode in FNmonitor:
                    toAdd = FNmonitor[childNode]
                    if parentNode not in FNmonitor:
                        FNmonitor[parentNode] = []
                    FNmonitor[parentNode] += toAdd
                    FNmonitor[parentNode] = list(set(FNmonitor[parentNode]))
                ### Update edges information
                edges = updateEdges(parentNode, childNode, edges)

                for eachEdge in edges:
                    if str(childNode) in (eachEdge):
                        print(childNode)
                        print(edges)
                        print(eachEdge)
                        
                        print("???")
                        exit()
                
                ### If the node is merged, skip this one
                if eachNode == childNode:
                    break
                    # i += 1
                    # j = EOL_out
                    # break
                
    allNodes = clearNodeList(allNodes) ### Cleanse allnodes
    
    return allNodes, edges, FNmonitor
   

def saveResult(repoName, allNodes, edges, FNmonitor, centrisResult, centrisTime, moduleTime, depsAnalysisTime):
    ##Deps, files, Nodes
    
    allNodes.sort(key=lambda x: x.OSS, reverse=True)
    
    sortedEdges = convertEdges(edges, allNodes)
    sortedEdges = sorted(sortedEdges, key=lambda v: v[0].split(" -> ")[0])
    
    # open(metaPath + "/" + "result_" + repoName, "r")
    timeRes = resPath + "/" + repoName + "_time" 
    nodeRes = resPath + "/" + repoName + "_nodes"
    edgesRes = resPath + "/" + repoName +  "_edges"
    
    OSS_files = {}
    OSS_roots = {}
    
    for eachOSS in centrisResult:
        OSS_files[eachOSS] = []
        OSS_roots[eachOSS] = []
    
    ### TimeRes
    with open(timeRes, "w") as fp:
        fp.write("centrisTime\t{:.2f}\n".format(centrisTime ))
        fp.write("moduleTime\t{:.2f}\n".format(moduleTime))
        fp.write("depsAnalysisTime\t{:.2f}\n".format(depsAnalysisTime))
        
    ### Nodes
    cnepsNodes = 0
    edgesCount =0 
    with open(nodeRes, "w") as fp:
        for eachNode in allNodes:
            cnepsNodes += 1
            if eachNode.OSS not in OSS_files:
                OSS_files[eachNode.OSS] = []
                OSS_roots[eachNode.OSS] = []
            OSS_files[eachNode.OSS] += eachNode.files
            OSS_roots[eachNode.OSS].append(eachNode.root)
            
            fp.write("{}\t@\t{}\n".format(eachNode.OSS, eachNode.root))
            fp.write("\t" + "parents: \n")
            for x in eachNode.parent:
                fp.write("\t\t" + x.OSS + "\t@\t" + x.root + "\n")
            fp.write("\t" + "childs: \n")
            for x in eachNode.child:
                edgesCount += 1
                fp.write("\t\t" + x.OSS + "\t@\t" + x.root + "\n")
            fp.write("\n")

    ### edges
    with open(edgesRes, "w") as fp:
        for eachEdge in sortedEdges:
            # print(eachEdge.split("\t")[0])
            fp.write( str(eachEdge).split("\t")[0] +  "\n\n" )



def main():
    inputPath = sys.argv[1]

    ### ParseRepoName used in various functions
    repoName = parseRepoName(inputPath)
    # print(repoName)
    ### Run CENTRIS
    
    centrisTime = time.time()
    print("! 0 Running CENTRIS for component analysis")
    if(os.path.exists(metaPath + "/" + repoName + "_centris")):
        print("! 0-1 Skipping using previous result")
    else: 
        centris.main(inputPath, repoName)
    centrisTime = time.time() - centrisTime
    print("Centris --- %s seconds ---" % (centrisTime)) 


    print("! 2 Reading OSS to generate modules")
    path2OSS, centrisResult = parseOSSinfo(inputPath, repoName)

    # else:
    moduleTime = time.time()
    moduleList, path2mod, hdr2path, meta = moduleGen(inputPath, repoName, path2OSS)
    OSSes = []
    for eachM in moduleList:
        if eachM.OSS not in OSSes:
            OSSes.append(eachM.OSS)
    
    ###### DEBVUG ######
    hdrs = []
    for eachM in moduleList:
        for eachF in eachM.files:
            if eachF.endswith(both):
                hdrs.append(eachF)
                break
    hdrs = list(set(hdrs))

    rootModules = []
    for eachM in moduleList:
        if(not eachM.parent):
            rootModules.append(eachM)

    ###### DEBVUG ######
    
    print("! 3 Generate nodes according to modules")
    allNodes, edges = genNodes(moduleList)
    moduleTime = time.time() - moduleTime
    print(" Module gen --- %s seconds ---" % (moduleTime) )
    # printNode(allNodes, [])
    # print("No dup? {}".format( len(allNodes) == len(set(allNodes))))
    # printAllNode(allNodes)
    # printNode(allNodes, [])
    
    
    
    print("! 4 Analyzing dependency...")

    
    FNmonitor = {}
    sameDirMergeTime = time.time()
    rootNodes, allNodes, edges, FNmonitor = mergeSameDirNodes(allNodes, edges, FNmonitor, meta)
    sameDirMergeTime = time.time() - sameDirMergeTime
    print("--- Merging Time %s seconds ---" % (sameDirMergeTime) )
    # rootNodes, allNodes, edges, FNmonitor = rootAnalysis(allNodes, edges, FNmonitor)    ### This is for reducing 
    # printNode(allNodes, [])
    # exit()

    # print("--- Merging Time %s seconds ---" % (depsAnalysisTime) )
    
    
    linkAnalysisTime = time.time()
    allNodes, edges, FNmonitor = linkedReuseAnalysis(repoName, allNodes, hdr2path, meta, edges)
    linkAnalysisTime = time.time() - linkAnalysisTime
    # printNode(allNodes, [])
    # print(len(allNodes))
    allNodes = originCandidGen(allNodes)
    print("--- Link analysis %s seconds ---" % (linkAnalysisTime) )
    # printNode(allNodes, [])
    # printNode(allNodes, [])
    # print(len(allNodes))
    depsAnalysisTime = time.time()
    allNodes, edges, FNmonitor = mergeSameSrcNodes(allNodes, edges, FNmonitor, hdr2path, meta)
    depsAnalysisTime = time.time() - depsAnalysisTime
    print("--- Merging time %s seconds ---" % (depsAnalysisTime) )
    
    depsAnalysisTime = depsAnalysisTime + linkAnalysisTime + sameDirMergeTime
    
    # allNodes, edges, FNmonitor = linkMergeAnalysis(repoName, allNodes, hdr2path, meta, edges)


### DEBUG CODE
    # printEdges(edges, allNodes)
    # depsAnalysis(allNodes, edges, FNmonitor)
    # print("No dup? {}".format( len(allNodes) == len   (set(allNodes))))
    # for eachNode in allNodes:
    #     if(eachNode in newNodes):
    #         print("DUP!!!: {}".format(eachNode))
    #     else:
    #         newNodes.append(eachNode)
    # print("Num nodes after deps analysis:{}".format(len(allNodes)))
    # print("\n\n\n------------DEBUG--------------\n\n\n")
    # printNode(allNodes, [])
    # print(len(allNodes))
### DEBUG CODE

    
    print("! 5 Analyzing paths")
    
    roots= {}
    for eachNode in allNodes:
        if eachNode.OSS not in roots:
            roots[eachNode.OSS] = []
        if eachNode.root not in roots[eachNode.OSS]:
            roots[eachNode.OSS].append(eachNode.root)
    
    for eachOSS in roots:
        print("OSS: {}".format(eachOSS))
        print("Root: ")
        for eachRoot in roots[eachOSS]:
            print('\t' + eachRoot)
        print()
    
    # depsAnalysisTime = time.time() - depsAnalysisTime
    # print("--- Deps analysis %s seconds ---" % (depsAnalysisTime) )
    # print(rootNodes)
    # print("Detected root nodes: {}".format(len(rootNodes)))
    # print("No dup? {}".format( len(rootNodes) == len(set(rootNodes))))
    # print("Num nodes after root analysis:{}".format(len(allNodes)))
    # print("No dup? {}".format( len(allNodes) == len(set(allNodes))))

    # printNode(allNodes, [])
    ### Save
    # visualizeGraph(repoName, allNodes)
    printEdges(edges, allNodes)
    saveResult(repoName, allNodes, edges, FNmonitor, centrisResult, centrisTime, moduleTime, depsAnalysisTime)


    # runserv(allNodes)

if __name__== "__main__":
    main()