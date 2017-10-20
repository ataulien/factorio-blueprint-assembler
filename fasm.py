import zlib
import base64
import sys 
import json
import math
import random
import pixelSignal

# ADD $5
# ADD [$5]

INSTRUCTIONVARIANT_IMMEDIATE = 1
INSTRUCTIONVARIANT_MEMORY = 2
INSTRUCTIONVARIANT_MEMREF = 3
INSTRUCTIONVARIANT_SIMPLE = 4
INSTRUCTIONVARIANT_IMMEDIATE_MEM = 5
INSTRUCTIONVARIANT_LABEL = 6
INSTRUCTIONVARIANT_MEMREF_G = 7
INSTRUCTIONVARIANT_REG_G = 8
INSTRUCTIONVARIANT_IMMEDIATE_2X = 9

instDict = {
	("LDA",  INSTRUCTIONVARIANT_IMMEDIATE)		: (1, {}),
	("LDB",  INSTRUCTIONVARIANT_IMMEDIATE)		: (2, {}),
	("JR",   INSTRUCTIONVARIANT_IMMEDIATE)		: (3, {}),
	("ADD",  INSTRUCTIONVARIANT_MEMORY)   		: (6, {}),
	("CMEM", INSTRUCTIONVARIANT_MEMORY)   		: (7, {}),
	("JR",   INSTRUCTIONVARIANT_IMMEDIATE)		: (3, {}),
	("CALU", INSTRUCTIONVARIANT_SIMPLE)   		: (5, {}),
	("ADD",  INSTRUCTIONVARIANT_IMMEDIATE_MEM)  : (10, {}),
	("JMP",  INSTRUCTIONVARIANT_LABEL)          : (3, {}),
	("BEQZ", INSTRUCTIONVARIANT_LABEL)          : (4, {}),
	("LDG",  INSTRUCTIONVARIANT_IMMEDIATE)      : (11, {}),
	("CG",   INSTRUCTIONVARIANT_SIMPLE)         : (12, {}),
	("LDG",   INSTRUCTIONVARIANT_MEMORY)        : (13, {}),
	("ADD",   INSTRUCTIONVARIANT_MEMREF_G)      : (14, {}),
	("CMEM",  INSTRUCTIONVARIANT_REG_G)         : (15, {}),
	("LDG",   INSTRUCTIONVARIANT_MEMREF_G)      : (16, {}),
	("LDA",   INSTRUCTIONVARIANT_MEMREF_G)     	: (17, {}),
	("LDB",   INSTRUCTIONVARIANT_MEMREF_G)     	: (18, {}),
	("LDA",   INSTRUCTIONVARIANT_REG_G)     	: (19, {}),
	("LDB",   INSTRUCTIONVARIANT_REG_G)     	: (20, {}),
	("LDA",   INSTRUCTIONVARIANT_MEMORY)     	: (21, {}),
	("LDB",   INSTRUCTIONVARIANT_MEMORY)     	: (22, {}),
	("SUB",   INSTRUCTIONVARIANT_MEMORY)     	: (23, {}),
	("MUL",   INSTRUCTIONVARIANT_MEMORY)     	: (24, {}),
	("DIV",   INSTRUCTIONVARIANT_MEMORY)     	: (25, {}),
	("MOD",   INSTRUCTIONVARIANT_MEMORY)     	: (26, {}),
	("POT",   INSTRUCTIONVARIANT_MEMORY)     	: (27, {}),
	("LSH",   INSTRUCTIONVARIANT_MEMORY)     	: (28, {}),
	("RSH",   INSTRUCTIONVARIANT_MEMORY)     	: (29, {}),
	("OUT",   INSTRUCTIONVARIANT_IMMEDIATE_2X)  : (30, {}),
}
	
class Instruction:
	@staticmethod
	def detectVariant(line):
		if line.find("#") != -1 and line.find("[") != -1:
			return INSTRUCTIONVARIANT_IMMEDIATE_MEM
		elif line.count("#") == 2:
			return INSTRUCTIONVARIANT_IMMEDIATE_2X
		elif line.find("#") != -1:
			return INSTRUCTIONVARIANT_IMMEDIATE
		elif line.find("[$GP]") != -1:
			return INSTRUCTIONVARIANT_MEMREF_G
		elif line.find("$GP") != -1:
			return INSTRUCTIONVARIANT_REG_G
		elif line.find("[") != -1:
			return INSTRUCTIONVARIANT_MEMORY
		#elif line.find("$") != -1:
		#	return INSTRUCTIONVARIANT_MEMORY
		elif line.find(".") != -1:
			return INSTRUCTIONVARIANT_LABEL
		elif line.find(" ") == -1:
			return INSTRUCTIONVARIANT_SIMPLE
		else:
			raise SyntaxError("Invalid syntax (duh) on Instruction type. Line: " + line)
	@staticmethod
	def makeInstructionSignals(line, labels, ic):
		parts = line.split(" ")
		values = line.replace("$", "").replace("#", "").replace(".", "").replace("[", "").replace("]", "").split(" ")
		var = Instruction.detectVariant(line)
		
		print(values)
		
		(opCode, signals) = instDict[(parts[0], var)]
		
		outSignals = {}
		outSignals["signal-O"] = opCode
							
		if var != INSTRUCTIONVARIANT_MEMREF_G and var != INSTRUCTIONVARIANT_REG_G:
			if len(values) > 1:
				if var == INSTRUCTIONVARIANT_LABEL:
					values[1] = str(labels[values[1]] - ic)
				
				outSignals["signal-blue"] = values[1].strip()
				
			if len(values) > 2:
				outSignals["signal-green"] = values[2].strip()
		
		return outSignals
			
	
	
# Global connection coupling list 
# Format: {"idx": x, "type": "green/red/...", "source": entity, "target": entity}
entityConnections = []

# Last iTick and iEnable combinators for connecting PC and Enable-lines
lastiTick = None 
lastiEnable = None
lastiOp = None
lastiAddr = None
lastiFlag = None

# Decodes a given base64-like Factorio Blueprint string
def decode(b64str):
	return json.loads(zlib.decompress(base64.decodestring(b64str[1:])))

# Encodes a given JSON-String to a base64-like Factorio Blueprint string
def encode(jsonStr):
	return "0" + base64.b64encode(zlib.compress(jsonStr, 9))
	
# Adds a connection to the global connection list
def addConnection(type, source, target, sourceidx, targetidx, sourcecircuitid = 0, targetcircuitid = 0):
	entityConnections.append({
			"sourceidx": sourceidx, 
			"targetidx": targetidx, 
			"targetcircuitid": targetcircuitid, 
			"sourcecircuitid": sourcecircuitid, 
			"type": type, 
			"source": source, 
			"target": target
		})
		
class Entity:
	def __init__(self):
		# Relative position on the map TODO: Relative to what?
		self.position = {"x": 0, "y": 0}
		
		# Increasing 1-Based index that represents the exact location
		# inside the "entities"-Array
		#
		# Will be filled on export
		self.entity_number = 0 
		
		# Instance name, eg. "decider-combinator"
		self.name = ""
		
		# Wire-Connections
		self.connections = {}
		
		# Direction
		self.direction = 2
		
	# Connects this entitiy connection at 'idx' to 'other' on 'otheridx' using a wire of type 'type'.
	#   idx      <int>: 1-Based index on where to connect the wire on the source 
	#   other <entity>: Other entity to connect to
	#   otheridx <int>: 1-Based index on where to connect the wire on the other 
	#   type  <string>: Possible settings: "green", "red"
	def connect(self, idx, other, otheridx, type,sourcecircuitid=0, targetcircuitid=0):
		addConnection(type, self, other, idx, otheridx, sourcecircuitid, targetcircuitid)
		
	# Intern
	def _intern_connectTo(self, idx, type, otherEntitiyID, othercircuit_id):
		if not str(idx) in self.connections:
			self.connections[str(idx)] = {}
		
		if not type in self.connections[str(idx)]:
			self.connections[str(idx)][type] = []
			
		self.connections[str(idx)][type].append({"entity_id": otherEntitiyID, "circuit_id": othercircuit_id})
		
	# Set position
	def setPosition(self, x, y):
		self.position = {"x": x, "y": y}
		
	# Get X-Coord
	def getPositionX(self):
		return self.position["x"]
		
	# Get Y-Coord
	def getPositionY(self):
		return self.position["y"]
		
	def setDirection(self, v):
		self.direction = v
			
# ---------------------------------------------------------------------
#                          MediumElectricPole
# ---------------------------------------------------------------------	
class MediumElectricPole(Entity):
	def __init__(self):
		Entity.__init__(self)
		self.name = "medium-electric-pole"
			
# ---------------------------------------------------------------------
#                          BigElectricPole
# ---------------------------------------------------------------------	
class BigElectricPole(Entity):
	def __init__(self):
		Entity.__init__(self)
		self.name = "big-electric-pole"
					
# ---------------------------------------------------------------------
#                          DeciderCombinator
# ---------------------------------------------------------------------
class ConstantCombinator(Entity):
	def __init__(self):
		Entity.__init__(self)
		self.name = "constant-combinator"
		self.control_behavior = {"filters":[]}
			
	# Adds a signal value to the constant combinator
	def addSignal(self, signal, count, type="virtual"):
		self.control_behavior["filters"].append({
			"count": count,
			"index": len(self.control_behavior["filters"]) + 1,
			"signal": {"type": type, "name": signal}
		})
			
# ---------------------------------------------------------------------
#                          ArithmeticCombinator
# ---------------------------------------------------------------------	
class ArithmeticCombinator(Entity):
	def __init__(self):
		Entity.__init__(self)
		self.name = "arithmetic-combinator"
		
		# Some default Values
		self.control_behavior = {
                    "arithmetic_conditions": {
						"constant": 0, 
                        "second_signal": {
                            "type": "virtual", 
                            "name": "signal-J"
                        }, 
                        "first_signal": {
                            "type": "virtual", 
                            "name": "signal-E"
                        }, 
                        "operation": "AND", 
                        "output_signal": {
                            "type": "virtual", 
                            "name": "signal-E"
                        }
                    }
				}
				
	# Virtual signal (ie. "signal-X")
	def setFirstSignal(self, signal):
		self.control_behavior["arithmetic_conditions"]["first_signal"]["name"] = signal;
		
	# Virtual signal (ie. "signal-X")
	def setSecondSignal(self, signal):
		self.control_behavior["arithmetic_conditions"]["second_signal"]["name"] = signal;
					
	# Virtual signal (ie. "signal-X")
	def setOutputSignal(self, signal):
		self.control_behavior["arithmetic_conditions"]["output_signal"]["name"] = signal;
	
	# Sets Constant. Clears second signal.
	def setConstant(self, const):
		if "second_signal" in self.control_behavior["arithmetic_conditions"]:
			del self.control_behavior["arithmetic_conditions"]["second_signal"]
		self.control_behavior["arithmetic_conditions"]["constant"] = const
				
	# Operation ("+", "AND", ...)
	def setOperation(self, op):
		self.control_behavior["arithmetic_conditions"]["operation"] = op;	
# ---------------------------------------------------------------------
#                          DeciderCombinator
# ---------------------------------------------------------------------
class DeciderCombinator(Entity):
	def __init__(self):
		Entity.__init__(self)
		self.name = "decider-combinator"
		
		# Some default values
		self.control_behavior = {
			"decider_conditions": {
                "copy_count_from_input": True, 
                "constant": 0, 
                "comparator": ">",
				"first_signal": {
                            "type": "virtual", 
                            "name": "signal-I"
                        },
				"output_signal": {
                            "type": "virtual", 
                            "name": "signal-J"
                        }
            }
		}
		
	# Virtual signal (ie. "signal-X")
	def setFirstSignal(self, signal):
		self.control_behavior["decider_conditions"]["first_signal"]["name"] = signal;
		
	# Virtual signal (ie. "signal-X")
	def setSecondSignal(self, signal):
		self.control_behavior["decider_conditions"]["second_signal"]["name"] = signal;
		
	# Sets Constant. Clears second signal.
	def setConstant(self, const):
		if "second_signal" in self.control_behavior["decider_conditions"]:
			del self.control_behavior["decider_conditions"]["second_signal"]
		self.control_behavior["decider_conditions"]["constant"] = const
		
	# Virtual signal (ie. "signal-X")
	def setOutputSignal(self, signal):
		self.control_behavior["decider_conditions"]["output_signal"]["name"] = signal;
		
	def setComperator(self, comp):
		self.control_behavior["decider_conditions"]["comparator"] = comp
	
			
# Produces an LDA or LDB instruction
# @param below  Where to place this instruction at
# @param reg    1 or 2 for "A" and "B"
# @param imm    Immediate Value
def inst_opcode_imm(bp, below, ic, opcode, imm):
	cc = ConstantCombinator()
	cc.addSignal("signal-V", imm)
	
	cc.addSignal("signal-O", opcode)
		
	if not below is None:
		cc.setPosition(below.getPositionX(), below.getPositionY() + 1)
	
	dc = DeciderCombinator()
	dc.setFirstSignal("signal-I")
	dc.setConstant(ic)
	dc.setComperator("=")
	dc.setOutputSignal("signal-everything")
	dc.setPosition(cc.getPositionX() + 2, cc.getPositionY())
	
	cc.connect(1, dc, 1, "green")
	
	bp.addEntity(cc)
	bp.addEntity(dc)
	
	return cc
	
# Produces an arith instruction
# @param below     Where to place this instruction at
# @param addr      Target address
def inst_opcode_addr(bp, below, ic, opcode, addr):
	cc = ConstantCombinator()
	cc.addSignal("signal-black", addr)
	cc.addSignal("signal-O", opcode)
		
	if not below is None:
		cc.setPosition(below.getPositionX(), below.getPositionY() + 1)
	
	dc = DeciderCombinator()
	dc.setFirstSignal("signal-I")
	dc.setConstant(ic)
	dc.setComperator("=")
	dc.setOutputSignal("signal-everything")
	dc.setPosition(cc.getPositionX() + 2, cc.getPositionY())
	
	cc.connect(1, dc, 1, "green")
	
	bp.addEntity(cc)
	bp.addEntity(dc)
	
	return cc
			
			
# ---------------------------------------------------------------------
#                       Build your blueprint here
# ---------------------------------------------------------------------		
def buildBlueprint(bp):
	return
		
def assemble(bp, linesAll):
	cc = None
	ic = 1
	
	# Jump labels
	labels = {}
	
	pole = MediumElectricPole()
	pole.setPosition(0,1)
	bp.addEntity(pole)
	
	lastInst = pole
	
	# Resolve labels, clean up comments, etc
	lines = []
	for l in linesAll:
		l = l.strip()
	
		if l.find("//") != -1:
			continue
			
		if l.strip() == "":
			continue
	
		# Labels are single words, ending with ":"
		if l[-1] == ":" and l.find(" ") == -1:
			labels[l[:-1]] = ic
			continue
			
		lines.append(l)
		ic = ic + 1
		
	# Actually parse code
	ic = 1
	for l in lines:
		signals = Instruction.makeInstructionSignals(l.strip(), labels, ic)
		
		cc = ConstantCombinator()
		cc.setPosition(ic, -1)
		cc.setDirection(4)
		
		for s in signals:
			cc.addSignal(s, signals[s])
		
		dc = DeciderCombinator()
		dc.setDirection(4)
		dc.setPosition(ic, 0.5)
		dc.setComperator("=")
		dc.setConstant(ic)
		dc.setFirstSignal("signal-I")
		dc.setOutputSignal("signal-everything")
		
		cc.connect(1, dc, 1, "red")
			
		lastInst.connect(1, dc, 1, "green")
		
		if lastInst is pole:
			lastInst.connect(1, dc, 2, "red")
		else:
			lastInst.connect(2, dc, 2, "red")
			
		lastInst = dc
			
		ic = ic + 1
		
		bp.addEntity(cc)
		bp.addEntity(dc)
		
		
		
# ---------------------------------------------------------------------
# -------------------------- Other Code Zone --------------------------
# ---------------------------------------------------------------------
class Blueprint:
	
	def __init__(self):
		self.blueprint = {}
		self.blueprint["entities"] = []
		
		# Not sure what exactly that is
		self.version = 64425164803
	
	# Adds an entity to the blueprint
	def addEntity(self, entity):
		self.blueprint["entities"].append(entity)
	
	# Enter entity-numbers, apply connections, etc
	# Automatically called on 'toJSON()'
	def finalize(self):
		# Enter 1-based entity-numbers
		for i in range(len(self.blueprint["entities"])):
			self.blueprint["entities"][i].entity_number = i + 1
		
		# Apply connections (Both ways)
		for c in entityConnections:
			c["source"]._intern_connectTo(c["sourceidx"], c["type"], c["target"].entity_number, c["targetidx"])
			c["target"]._intern_connectTo(c["targetidx"], c["type"], c["source"].entity_number, c["sourceidx"])
	
	# Converts this class to a JSON-String
	def toJSON(self):	
		self.finalize()
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

	
if len(sys.argv) < 2:
	print("Usage: python fasm.py [-e|-d] args")
	sys.exit(0)


if sys.argv[1] == "-e":
	# Encode a file
	with open(sys.argv[2], 'r') as f:
		js = f.read().replace('\n', '').replace('\r', '').replace(' ', '')
		
		out = "0" + base64.b64encode(zlib.compress(js.encode(), 9))
		print(out)
elif sys.argv[1] == "-d":
	# Decode a file
	bs = sys.argv[2]
	
	print(json.dumps(decode(bs), indent=4))
elif sys.argv[1] == "-t":
	# Test
	
	bp = Blueprint()
	
	buildBlueprint(bp)
	
	if "-e" in sys.argv:
		print(encode(bp.toJSON()))
	else:
		print(bp.toJSON())
elif sys.argv[1] == "-c":
	bp = Blueprint()
	
	with open(sys.argv[2]) as f:
		assemble(bp, f.readlines())
		
		if "-e" in sys.argv:
			print(encode(bp.toJSON()))
		else:
			print(bp.toJSON())
elif sys.argv[1] == "-sym":
	bp = Blueprint()
	for i in range(10):
		cc = ConstantCombinator()
		cc.setPosition(i, 0)
		for s in pixelSignal.makeSymbol(i):
			cc.addSignal(s, 1, "item")
		bp.addEntity(cc)
		
	if "-e" in sys.argv:
		print(encode(bp.toJSON()))
	else:
		print(bp.toJSON())
# bp = """0eNpljtEKwjAMRf/lPleZYxvYXxGRTYMEtrS03bCM/rtt9yL4lhtyzs2OaV7JOpYAvYOfRjz0bYfnt4xz2YVoCRocaIGCjEtJzkzGGheQFFhe9IG+pLsCSeDAdDhqiA9Zl4lcPvinFazxGTBSmrLk1Jx7hXgMqRhrr/55U2Ej5ysydF3bXZt26IeUvneaQrk="""

# ------- MAIN PROGRAM -------

#version = bp[0]

#data = json.loads(zlib.decompress(base64.decodestring(bp[1:])))



#print(json.dumps(data, indent=4))

#return "0" + str(base64.b64encode(zlib.compress(json.dumps(bp_json_obj,separators=(',', ':')).encode('utf-8'),9)),'utf-8')
