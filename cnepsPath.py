import os

ctagsPath = "./bin/ctags"
resPath = "./cneps-res"
metaPath = "./cneps-meta"
# trashPath = "./trash"
codeList = (".c", ".cc", ".cpp")
hdrList = (".h", ".hxx", ".hpp")
# both = codeList + hdrList

shouldMake 	= [resPath, metaPath]
for eachRepo in shouldMake:
	if not os.path.isdir(eachRepo):
		os.mkdir(eachRepo)