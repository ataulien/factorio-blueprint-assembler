#Signals for an 4x8 Display cell

WIDTH = 4
HEIGHT = 8

pixelSignals = {
	(0,7):  "wooden-chest",
	(0,6):  "iron-chest",
	(0,5):  "steel-chest",
	(0,4):  "storage-tank",
	(0,3):  "transport-belt",
	(0,2):  "fast-transport-belt",
	(0,1):  "express-transport-belt",
	(0,0):  "underground-belt",
	(1,7):  "fast-underground-belt",
	(1,6):  "express-underground-belt",
	(1,5): "splitter",
	(1,4): "fast-splitter",
	(1,3): "express-splitter",
	(1,2): "burner-inserter",
	(1,1): "inserter",
	(1,0): "long-handed-inserter",
	(2,7): "fast-inserter",
	(2,6): "filter-inserter",
	(2,5): "stack-inserter",
	(2,4): "stack-filter-inserter",
	(2,3): "small-electric-pole",
	(2,2): "medium-electric-pole",
	(2,1): "big-electric-pole",
	(2,0): "substation",
	(3,7): "pipe",
	(3,6): "pipe-to-ground",
	(3,5): "pump",
	(3,4): "rail",
	(3,3): "train-stop",
	(3,2): "rail-signal",
	(3,1): "rail-chain-signal",
	(3,0): "locomotive"
}
# 4,5,6,7,8,11,12,15,16
symbols = {
0:[
	[0,0,0,0],
	[1,1,1,1],
	[1,0,0,1],
	[1,0,0,1],
	[1,0,0,1],
	[1,0,0,1],
	[1,1,1,1],
	[0,0,0,0],
],
1:[
	[0,0,0,0],
	[1,1,1,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0],
	[0,0,1,0],
	[1,1,1,1],
	[0,0,0,0],
],
2:[
	[0,0,0,0],
	[0,1,1,0],
	[1,0,0,1],
	[0,0,1,0],
	[0,1,0,0],
	[1,0,0,0],
	[1,1,1,1],
	[0,0,0,0],
],
3:[
	[0,0,0,0],
	[0,1,1,0],
	[1,0,0,1],
	[0,0,0,1],
	[0,0,1,0],
	[0,0,0,1],
	[1,0,0,1],
	[0,1,1,0],
],
4:[
	[0,0,0,0],
	[1,0,0,0],
	[1,0,0,0],
	[1,0,0,0],
	[1,0,1,0],
	[1,1,1,1],
	[0,0,1,0],
	[0,0,1,0],
],
5:[
	[0,0,0,0],
	[1,1,1,1],
	[1,0,0,0],
	[1,1,1,0],
	[0,0,0,1],
	[0,0,0,1],
	[1,1,1,0],
	[0,0,0,0],
],
6:[
	[0,0,0,0],
	[0,1,1,0],
	[1,0,0,1],
	[1,0,0,0],
	[1,1,1,0],
	[1,0,0,1],
	[1,0,0,1],
	[0,1,1,0],
],
7:[
	[0,0,0,0],
	[1,1,1,1],
	[0,0,0,1],
	[0,0,1,0],
	[0,1,0,0],
	[0,1,0,0],
	[0,1,0,0],
	[0,1,0,0],
],
8:[
	[0,0,0,0],
	[0,1,1,0],
	[1,0,0,1],
	[1,0,0,1],
	[0,1,1,0],
	[1,0,0,1],
	[1,0,0,1],
	[0,1,1,0],
],
9:[
	[0,0,0,0],
	[0,1,1,0],
	[1,0,0,1],
	[1,0,0,1],
	[0,1,1,1],
	[0,0,0,1],
	[1,0,0,1],
	[0,1,1,0],
]
}

# Returns the matching signal to the given pixel coords
def getSignal(x, y):
	return pixelSignals[(x,y)]
	
def makeSymbol(sym):
	arr = []
	for y in range(8):
		for x in range(4):
			v = symbols[sym][y][x]
			if v != 0:
				arr.append(getSignal(x,y))
	
	return arr
	