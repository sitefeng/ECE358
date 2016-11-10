import lab2_queue_for_lab2
import uuid
import sys
import random

kSecondsPerTick = 10**(-8)
kSenseBitTimes = 96
kJammingBitTimes = 48
kBEBMaxI = 10

class CSMAPacket(Packet):
	def __init__(self, length, time, srcNodeIndex, destNodeIndex):
		super(CSMAPacket, self).__init__(length, time)
		self.srcNodeIndex = srcNodeIndex
		self.destNodeIndex = destNodeIndex
		self.uid = uuid.uuid4()

class CSMABus:

	# S === propSpeed
	def __init__(self, nodeDistance, propSpeed=2*(10**8), lanSpeed=10**6):
		self.packets = {}
		self.nodeDistance = nodeDistance
		self.propSpeed = propSpeed
		self.lanSpeed = lanSpeed

	def physicalDist(self, nodeIndex1, nodeIndex2):
		return abs(nodeIndex1 - nodeIndex2) * self.nodeDistance

	# Assuming nodes are linearly arranged on a bus, 
	# node is sequencially index from 1 to N from left to right
	def isBusyForNode(self, nodeIndex, currTime):
		isBusy = False
		for key, packet in self.packets.iteritems():
			physicalDist = self.physicalDist(nodeIndex, packet.srcNodeIndex)
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

	# node: Integer
	def packetArrivedForNode(self, nodeIndex, currTime):
		for key, packet in self.packets.iteritems():
			if packet.destNodeIndex == nodeIndex:
				
				physicalDist = self.physicalDist(packet.destNodeIndex, packet.srcNodeIndex)
				firstPassTime = physicalDist / self.propSpeed + packet.creationTime
				lastPassTime = firstPassTime + packet.length / self.lanSpeed

				# see if the packet has been fully processed
				if lastPassTime >= currTime:
					return packet
		return None


# Carrier Sense Multiple Access with collision detection(CSMA/CD)
class LAN:
	def __init__(self, N, P=1, W= 10**6, L =1500*8):
		self.numNodes = N #Number of computers [var]
		self.lanSpeed = W #Speed of the LAN (bits/s)[fixed]
		self.avgArrival = 0 #Average arrival rate (pkts/s)[var]
		self.packetLength = L #Packet Length (bits)[fixed]

class Node:

    def __init__(self, index, LAN, L = 1500*8):
    	self.index = index
    	self.lan = lan
    	self.lanSpeed = lan.lanSpeed
    	self.packetLength = L #L Packet Length (bits)[fixed]

    # iVal is an integer
    # Returns number of ticks required for the wait
    def generateRandomWaitTicks(self, iVal):
    	if iVal >10:
    		print("BEB i value should be less or equal to 10")
    		return None

    	randVal = random.randint(0, 2**i - 1)
    	Tp = 512 / self.lanSpeed
    	randTime = Tp * randVal
    	ticksReq = randTime / kSecondsPerTick
    	return ticksReq

    def requiredSensingTicks(self):
    	return kSenseBitTimes/lanSpeed/kSecondsPerTick

    def requiredJammingTicks(self):
    	return kJammingBitTimes/lanSpeed/kSecondsPerTick

    def requiredSendingTicks(self):
    	return self.packetLength/lanSpeed/kSecondsPerTick


class NodeNonAndPPersistent(Node):

	class SendState:
		UNKNOWN = 0
		SENSING = 1
		WAITING = 2
		SENDING = 3
		JAMMING = 4
		POSTJAMMING = 5

    class SendStatus:
    	SENDING = 0
    	SUCCESS = 1
    	COLLISION = -1

    def __init__(self, W, csmaBus, shouldSenseWait, pPersistentProbability):
    	super(NodeNonPersistent, self).__init__(W)

    	self.avgArrival = 0 #A Average arrival rate (pkts/s)[var]

    	self.csmaBus = csmaBus
    	self.sendQueue = PacketQueue()

    	self.requiredStateTicks = 0
    	self.currentI = 0

    	self.sendState = SendState.UNKNOWN

    	self.jammingPacket = None

    	# P-Persistent or Non-Persistent Characteristics
    	self.shouldSenseWait = shouldSenseWait
    	self.pPersistentProbability = pPersistentProbability


    def registerTick(self, currTime):
    	sendPacketForTick(currTime)
    	receivePacketForTick(currTime)

    	
    def sendPacketForTick(self, currTime):

    	if self.sendQueue.hasPacket():
    		if self.sendState is SendState.UNKNOWN:
    			self.sendState = SendState.SENSING
    			self.requiredStateTicks = self.requiredSensingTicks()

    		elif self.sendState is SendState.SENSING:
    			if self.requiredStateTicks <= 0:
    				self.sendState = SendState.SENDING
    				return

    			self.requiredStateTicks -= 1

    			if self.senseMediumBusy(currTime):
    				waitTicks = self.generateRandomWaitTicks(currentI)
    				if not shouldSenseWait:
    					waitTicks = 0

    				self.sendState = SendState.WAITING
    				self.requiredStateTicks = waitTicks
    			else: # not sensed busy yet
    				pass

    		elif self.sendState is SendState.WAITING:
    			if waitTicks > 0:
    				waitTicks -= 1
    			else: # Finish waiting
	    			self.sendState = SendState.UNKNOWN

    		elif self.sendState is SendState.SENDING:

    			# 0- sending still, 1: success, -1: collision
    			status = self.sendPacketForTick(currTime)
    			if status == SendStatus.SENDING:
    				pass
    			elif status == SendStatus.SUCCESS:
    				self.sendState = SendState.UNKNOWN
    				self.currentI = 0
    			else: #not success (collision state)
    				self.currentI += 1
    				self.sendState = SendState.JAMMING
    				self.requiredStateTicks = self.requiredJammingTicks()

    		elif self.sendState is SendState.JAMMING:
    			if self.requiredStateTicks == self.requiredJammingTicks():
    				self.jammingPacket = CSMAPacket(kJammingBitTimes, currTime, self.index, -1)
    				self.csmaBus.addPacket(self.jammingPacket)
    				
				elif self.requiredStateTicks <= 0: #Finished Jamming
    				self.sendState = SendState.POSTJAMMING
    				self.csmaBus.removePacket(self.jammingPacket.uid)
    				return

    			self.requiredStateTicks -= 1
    			

    		elif self.sendState is SendState.POSTJAMMING:
    			self.currentI += 1
    			if self.currentI > kBEBMaxI:
    				self.currentI = 10
    			self.requiredStateTicks = generateRandomWaitTicks(self.currentI)

    			if self.requiredStateTicks > 0:
    				self.requiredStateTicks -= 1
    			else:
	    			self.sendState = SendState.UNKNOWN
    	else:
    		pass # no packet to send


    def receivePacketForTick(self, currTime):
    	packet = self.csmaBus.packetArrivedForNode(self)
    	if packet is not None:
    		self.csmaBus.removePacket(packet.uid)


    # returns True if the medium is busy, vice versa
    def senseMediumBusy(self, currTime):
    	return self.csmaBus.isBusyForNode(self, currTime)

    def sendPacketForTick(self, currentTime):
    	self.requiredStateTicks = requiredSendingTicks()
    	if senseMediumBusy(currentTime):
    		status = SendStatus.COLLISION
    	elif self.requiredStateTicks >= 0:
    		self.requiredStateTicks -= 1
    		status = SendStatus.SENDING
    	else:
    		destNodeIndex = random.randint(1, self.lan.numNodes)
    		while destNodeIndex == self.index:
    			destNodeIndex = random.randint(1, self.lan.numNodes)

    		newPacket = CSMAPacket(self.packetLength, currentTime, self.index, destNodeIndex):
    		self.csmaBus.addPacket(newPacket)
			status = SendStatus.SUCCESS

    	return status



class NodePPersistent(Node):
	def __init__(self, P):
		super(NodePPersistent, self).__init__(W)
		self.PPersistentProbability = P #Persistent CSMA param
    

def main(args):
	


if __name__ == "__main__":
	main(sys.argv[1:])


 

 

