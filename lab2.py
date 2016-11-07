import lab1_queue
import uuid

class CSMAPacket(Packet):
	def __init__(self, length, time, srcNode, destNode):
		super(CSMAPacket, self).__init__(length, time)
		self.srcNode = srcNode # just a integer index number
		self.destNode = destNode
		self.uid = uuid.uuid4()

class CSMABus:

	# S === propSpeed
	def __init__(self, nodeDistance, propSpeed=2*(10**8), lanSpeed=10**6):
		self.packets = {}
		self.nodeDistance = nodeDistance
		self.propSpeed = propSpeed
		self.lanSpeed = lanSpeed

	# Assuming nodes are linearly arranged on a bus, 
	# node is sequencially index from 1 to N from left to right
	
	def isBusyForNode(self, node, currTime):
		isBusy = False
		for key, packet in self.packets.iteritems():
			physicalDist = abs(node-packet.srcNode) * self.nodeDistance
			firstPassTime = physicalDist / self.propSpeed + self.packet.creationTime
			lastPassTime = firstPassTime + self.packet.length / self.lanSpeed

			if firstPassTime <= currTime <= lastPassTime:
				isBusy = True

		return isBusy

	# self, CSMAPacket
	def addPacket(self, packet):
		self.packets[packet.uid] = packet

	def removePacket(self, packetUid):
		pkt = self.packets[packetUid]
		del self.packets[packetUid]
		return pkt


# Carrier Sense Multiple Access with collision detection(CSMA/CD)
class LAN:
	def __init__(self, N, P=1, W= 10**6, L =1500*8):
		self.numNodes = N #Number of computers [var]
		self.lanSpeed = W #Speed of the LAN (bits/s)[fixed]
		self.avgArrival = 0 #Average arrival rate (pkts/s)[var]
		self.packetLength = L #Packet Length (bits)[fixed]

class Node:
    #Constants
    secondsPerTick = 0.01

    # Input Variables
    avgArrival = 0 #A Average arrival rate (pkts/s)[var]
    packetLength = 0 #L Packet Length (bits)[fixed]


class NodeNonPersistent(Node):

    def __init__(self):
    	self.avgArrival = 0 #A Average arrival rate (pkts/s)[var]
    	self.packetLength = 0 #L Packet Length (bits)[fixed]


    def registerTick(self):
    	pass
    	
		

class NodePPersistent(Node):
	def __init__(self, P):
		self.PPersistentProbability = P #Persistent CSMA param
    





 

 

