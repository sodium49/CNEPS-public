import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import cnepsPath

ctagsPath = cnepsPath.ctagsPath
resPath = cnepsPath.resPath
metaPath = cnepsPath.metaPath
codeList = cnepsPath.codeList
hdrList = cnepsPath.hdrList
both = codeList + hdrList

class gnode():
    def __init__(self):
        self.OSS = "unknown"   ### This is list type because it can be multiple 
        self.root = ""
        self.src = [None]
        # self.intert = []
        self.files = [] ### Files contained in this node, can be multiple
        self.child = [] ### Link to Child nodes 
        self.parent = []    ### Link to parent nodes 
        self.deps = []
        # self.copied = []

    def insM(self, module, allNodes, edges, path2nodes=None): ### Use it only on graph gen phase
        ### Parent module
        for eachFile in module.files:
            if eachFile not in self.files:
                self.files.append(eachFile)
                
        ## Child Modules
        for eachChildM in module.sub:
            # if eachChildM.OSS in self.child:
            insPosFound = False
            targetNode = findOSSnodes(self.child, eachChildM.OSS)
            if targetNode:
                ### Check if matching node exists / Use path information
                # modulePath = "/".join(module.path.split("/")[:-1])
                modulePath = module.root
                for eachTargetNode in targetNode:
                    if(eachTargetNode.root == modulePath):
                        insPosFound = True
                        eachTargetNode.insM(eachChildM, allNodes, path2nodes)
                        #break Insert to all positoin, it will be integrated anyway
                        
            if not insPosFound:
                ### Make new node for target sub module
                newSubNode = gnode()
                newSubNode.src = [self]
                newSubNode.OSS = eachChildM.OSS
                newSubNode.root = self.root
                newSubNode.files = eachChildM.files
                newSubNode.parent = [self]
                allNodes.append(newSubNode)
                """
                if(path2nodes):### Used for path gen algorithm
                    if(self.root not in path2nodes):
                        path2nodes[self.root] = {}
                    if eachChildM.OSS not in path2nodes[self.root]:
                        path2nodes[self.root][eachChildM.OSS] = []
                path2nodes[self.root][eachChildM.OSS] += [newSubNode]
                """
                
                ### At this moment, there is no sub-sub node
                self.child.append(newSubNode)
                edgeStr = "{} -> {}".format(self, newSubNode)
                edges[edgeStr] = "inc"
                # print(edges)
                # print(edgeStr)

    def processSubM(self, module):
        """Input: parent module"""
        for eachSubM in module.sub:
            ### Get sub nodes
            OSSList = self.getSubNodeOSS()
            ### Get sub oss list of parent node
            if eachSubM.OSS not in OSSList:
                
                newSubNode = eachSubM.node
                ### Make parent-child relationship
                newSubNode.parent.append(self)
                self.child.append(newSubNode)
            
            else:
                subNode = self.getTargetSubNode(eachSubM.node.OSS)
                if(subNode == None):
                    print("ERR")
                    exit()
                ### Incase same node, but considered differently, combine them
                if(eachSubM not in subNode.module):
                    # print("COMBINING!!!")
                    self.combTwoSubNodes(subNode, eachSubM.node)
                    
    def getSubNodeOSS(self):
        ret = []
        for eachChildNode in self.child:
            if(eachChildNode.OSS not in ret):
                ret.append(eachChildNode.OSS)

        return ret

    def getTargetSubNode(self, OSS):

        for eachChildNode in self.child:
            if(eachChildNode.OSS == OSS):
                return eachChildNode
        return None

def visualizeGraph(repoName, allNodes):
    
    G = nx.DiGraph()
    nodes = []
    edges = []
    node2name = {}
    OSScounts = {}
    
    ### Vertex
    for eachNode in allNodes:
        if eachNode not in node2name:
            node2name[eachNode] = eachNode.OSS
        if eachNode.OSS in OSScounts:
            OSScounts[eachNode.OSS] += 1
            node2name[eachNode] = eachNode.OSS + OSScounts[eachNode.OSS]
        G.add_node(eachNode)
        
    ### 
    for eachNode in allNodes:
        for eachChild in eachNode.child:
            targetEdge = (eachNode, eachChild)
            if targetEdge not in edges:
                G.add_edge(eachNode, eachChild)
                edges.append(targetEdge)
                
    # nx.draw(G, with_labels=True, node_color="lightblue", font_weight="bold", node_size=1500, arrowsize=20)
    plt.figure(figsize=(12, 12))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue")


    plt.savefig(resPath + "/" + "graph_" + repoName + ".png", format="PNG")
    plt.close()

def networkx_to_plotly(G):
    # Get node positions
    pos = nx.spring_layout(G)

    # Extract node and edge information
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]

    # Create a trace for edges
    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color="gray"), hoverinfo="none", mode="lines")

    # Map node degrees to colors using the viridis colormap
    degrees = [degree for _, degree in G.degree()]
    max_degree = max(degrees)
    colors = plt.get_cmap("viridis")(degrees)
    colors = [f"rgba({r},{g},{b},{a})" for r, g, b, a in (colors * 255).astype(int)]

    # Create a trace for nodes
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        marker=dict(color=colors, size=10),
        text=list(G.nodes()),
    )

    # Create a layout for the plot
    layout = go.Layout(showlegend=False, hovermode="closest")

    return go.Figure(data=[edge_trace, node_trace], layout=layout)

def convertEdges(edges, allNodes):
    newEdges = ()
    for eachEdge in edges:
        # print(eachEdge, edges[eachEdge])
        # print(allNodes)
        n1, n2 = eachEdge.split(" -> ")
        n1 = (n1.split(" ")[-1].split(">")[0])
        n1 = int(n1, 16)
        n2 = (n2.split(" ")[-1].split(">")[0])
        n2 = int(n2, 16)
        
        for eachNode in allNodes:
            if(id(eachNode) == n1):
                n1 = eachNode
            if(id(eachNode) == n2):
                n2 = eachNode
        # print(n1, n2)
        # try:
        n1 = n1.OSS + "@" + n1.root
        n2 = n2.OSS + "@" + n2.root
        # except:
            # print(n1, n2, eachNode)
        
        # print("{} -> {}".format(n1, n2), edges[eachEdge])
        newEdges += ("{} -> {}\t{}".format(n1, n2, edges[eachEdge]), )
    # print(newEdges)
    return newEdges

def printEdges(edges, allNodes):
    for eachEdge in edges:
        # print(eachEdge, edges[eachEdge])
        # print(allNodes)
        n1, n2 = eachEdge.split(" -> ")
        n1_debug = n1
        n2_debug = n2
        n1 = (n1.split(" ")[-1].split(">")[0])
        n1 = int(n1, 16)
        n2 = (n2.split(" ")[-1].split(">")[0])
        n2 = int(n2, 16)
        
        for eachNode in allNodes:
            if(id(eachNode) == n1):
                n1 = eachNode
            if(id(eachNode) == n2):
                n2 = eachNode
        # print(n1, n2)
        try:
            n1 = n1.OSS + "@" + n1.root
            n2 = n2.OSS + "@" + n2.root
        except:
            print(n1_debug, n2_debug)
            exit()
        
        print("{} -> {}".format(n1, n2))

def findEdge(node1, node2, edges):
    ret = []
    edgeStr1 = "{} -> {}".format(node1, node2)
    edgeStr2 = "{} -> {}".format(node2, node1)
    
    if edgeStr1 in edges:
        ret.append(edgeStr1)
    
    if edgeStr2 in edges:
        ret.append(edgeStr2)
    
    return ret

def updateEdges(node1, node2, edges):
    """change node1 to node 2"""
    ret = edges.copy()

    for eachEdge in edges:
        ### This edge will be deleted 
        ### merged, link between different component -> link between "same" component
        if str(node2) in eachEdge and str(node1) in eachEdge:
            del ret[eachEdge]

        elif str(node2) in eachEdge: ## and str(node1) not in eachEdge:
            childEdgeType = edges[eachEdge]
            parentEdgeStr = eachEdge.replace(str(node2), str(node1))

            ### If this edge already exists, wheter copied or not, if type differs, merge them
            if parentEdgeStr in ret:
                parentEdgeType = ret[parentEdgeStr]
                if parentEdgeType != childEdgeType:
                    if childEdgeType == "inc\tlink":
                        ret[parentEdgeStr] = childEdgeType
                    if parentEdgeType == "inc" or parentEdgeType == "link":
                        ret[parentEdgeStr] = "inc\tlink"
                    elif parentEdgeType == "inc\tlink":
                        pass
                    else:
                        print(parentEdgeType)
                        print(childEdgeType)
                        print("err")
                        exit()
                del ret[eachEdge]
            
            else:
                ret[parentEdgeStr] = childEdgeType
                del ret[eachEdge]

    return ret

def printAllNode(allNodes):
    for eachNode in allNodes:
        print(eachNode)

        print("\t" + eachNode.OSS + '\t' + eachNode.root)
        # print("\t" + eachNode.root)
        print("\t\t" + "files: ")
        for x in eachNode.files:
            print("\t\t\t", x)
        print()
        print("\t\t" + "parents: ")
        for x in eachNode.parent:
            print("\t\t\t", x.OSS + "\t" + str(x) + "\t" + x.root)
        print()
        print("\t\t" + "childs: ")
        for x in eachNode.child:
            print("\t\t\t", x.OSS + "\t" + str(x) + "\t" + x.root)

        
        # for eachFile in eachNode.files:
        #     print("\t"*level + eachFile)

        # if (eachNode.child):
            # printNode(eachNode.child, printedNodes, level+1)
        print()

def printNode(allNodes, printedNodes, level=0):
    for eachNode in allNodes:
        if eachNode in printedNodes:
            continue
        printedNodes.append(eachNode)
        print("\t"*level , eachNode)

        print("\t"*level + eachNode.OSS)
        print("\t"*level + eachNode.root)
        print("\t"*level + "Source: ", eachNode.src)
        if eachNode.src:
            print("\t"*(level+1), eachNode.src)
            for eachSrcNode in eachNode.src:
                if eachSrcNode:
                    print("\t"*(level+2) + eachSrcNode.OSS)
                    print("\t"*(level+2) + eachSrcNode.root)
        print("\t"*level + "files: ")
        for x in eachNode.files:
            print("\t"*(level+1), x)
        print("\t"*level + "parents: ")
        for x in eachNode.parent:
            print("\t"*(level+1), x.OSS + "\t" + str(x) + "\t" + x.root)
        print("\t"*level + "childs: ")
        for x in eachNode.child:
            print("\t"*(level+1), x.OSS + "\t" + str(x) + "\t" + x.root)

        
        # for eachFile in eachNode.files:
        #     print("\t"*level + eachFile)

        if eachNode.child:
            printNode(eachNode.child, printedNodes, level+1)
        print()

def isIntNodes(n1, n2):
    """
        Merge two different OSS nodes into one node
    """
    pass

def combNodes(n1, n2):
    pass

def updatePath2Node(path2node, targetNode, updateNode):
    for eachHdr in path2node:
        if(targetNode in path2node[eachHdr]):
            path2node[eachHdr][path2node[eachHdr].index(targetNode)] = updateNode
            path2node[eachHdr] = list(set(path2node[eachHdr])) ### Delete if dups

def checkIntertDetected(eachNode):
    # childNodes = set(eachNode.child)
    # parentNodes = set(eachNode.parent)
    intNodes = [n for n in eachNode.child if n in eachNode.parent]
    if (intNodes):
        print("intert detected!!")
        print(intNodes)
        for eachIntNode in intNodes:
            intNode = eachIntNode
            ### Detlete interted node from child, parent of each other
            # if eachNode not in intNode.parent or \
            #     eachNode not in intNode.child or \
            #     intNode not in eachNode.parent or \
            #     intNode not in eachNode.child:
            #     print("???")
            #     exit()
            eachNode.child.pop(eachNode.child.index(intNode))
            eachNode.parent.pop(eachNode.parent.index(intNode))
            intNode.child.pop(intNode.child.index(eachNode))
            intNode.parent.pop(intNode.parent.index(eachNode))

            ### Make in intert node for each other
            eachNode.intert.append(intNode)
            intNode.intert.append(eachNode)




def mergeNode(n1, n2, allNodes, path2nodes=None, newRoot=False):
    """
        Merge two same OSS nodes into one node
        Assumes n1 is new root
    """
    
    ### OSS
    # for eachOSS in n2.OSS:
    #     if eachOSS not in n1.OSS:
    #         n1.OSS.append(eachOSS)
    ### Root - change only when newRoot needed
    if newRoot:
        n1.root = newRoot
    
    ### File
    # for eachFile in n2.files:
    #     if eachFile not in n1.files:
    #         n1.files.append(eachFile)
    n1.files = list(set(n1.files + n2.files))
            
    ### src
    n1.src = list(set(n1.src + n2.src))
    if len(n1.src) > 1 and None in n1.src:
        n1.src.pop(n1.src.index(None))

    ### Child
    for eachChild in n2.child:
        if eachChild == n1:
            eachChild.parent.pop(eachChild.parent.index(n2))
            eachChild.parent = list(set(eachChild.parent))
            continue

        
        if n2 in eachChild.src:
            eachChild.src[eachChild.src.index(n2)] = n1
            eachChild.src = list(set(eachChild.src))
            
        if  eachChild not in n1.child :
            n1.child.append(eachChild)
            
        # print("Chainging Child!")
        # print(eachChild.parent)
        eachChild.parent[eachChild.parent.index(n2)] = n1
        eachChild.parent = list(set(eachChild.parent))
        # print(eachChild.parent)

    ### Parent
    for eachParent in n2.parent:
        if(eachParent == n1):
            # print("???")
            eachParent.child.pop(eachParent.child.index(n2))
            eachParent.child = list(set(eachParent.child))
            continue
            # exit()

        
        if n2 in eachParent.src:
            eachParent.src[eachParent.src.index(n2)] = n1
            eachParent.src = list(set(eachParent.src))

        if eachParent not in n1.parent:
            n1.parent.append(eachParent)
        eachParent.child[eachParent.child.index(n2)] = n1
        eachParent.child = list(set(eachParent.child))
        # print(eachParent.child)
        
    ### Deps Logs
    n1.deps += n2.deps
    n1.deps = list(set(n1.deps))
    
    allNodes[allNodes.index(n2)] = None
    return allNodes



def clearNodeList(allNodes):
    allNodes = list(filter(None, allNodes)) ### Cleanse allnodes
    return allNodes

def findOSSnodes(nodeList, OSS):
    ### Find OSS in nodeList
    nodes = []
    for eachNode in nodeList:
        if(eachNode.OSS == OSS):
            nodes.append(eachNode)
            # node = eachNode

    return nodes

def isIntert(curNode, targetNode):
    if curNode in targetNode.child or targetNode in curNode.intert:
        return True
    else:
        return False

def processIntert(curNode, targetNode):
    if curNode in targetNode.child:
        ### Change child state to intert state
        targetNode.child.pop(targetNode.child.index(curNode))
        ### Change parent state to intert state
        curNode.parent.pop(curNode.parent.index(targetNode))
    targetNode.intert.append(curNode)
    curNode.intert.append(targetNode)




