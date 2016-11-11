import lab2_queue_for_lab2
import uuid
import sys
import random

# Carrier Sense Multiple Access with collision detection(CSMA/CD)

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
	def __init__(self, nodeDistance=10, propSpeed=2*(10**8), lanSpeed=10**6):
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


class Node:

    def __init__(self, lanSpeed, index, L):
    	self.index = index
    	self.lanSpeed = lanSpeed
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
    	return kSenseBitTimes/self.lanSpeed/kSecondsPerTick

    def requiredJammingTicks(self):
    	return kJammingBitTimes/self.lanSpeed/kSecondsPerTick

    def requiredSendingTicks(self):
    	return self.packetLength/self.lanSpeed/kSecondsPerTick


class NodeNonAndPPersistent(Node):

	class SendState:
		IDLE = 0
		SENSING = 1
		WAITING = 2
		PRESENDING = 3
		PRESENDWAITING = 4
		SENDING = 5
		JAMMING = 6
		POSTJAMMING = 7

    class SendStatus:
    	SENDING = 0
    	SUCCESS = 1
    	COLLISION = -1

    def __init__(self, index, W, L, csmaBus, shouldSenseWait, pPersistentProbability):
    	super(NodeNonPersistent, self).__init__(W, index, L)

    	self.avgArrival = 0 #A Average arrival rate (pkts/s)[var]

    	self.csmaBus = csmaBus
    	self.sendQueue = PacketQueue(self.avgArrival, L, queueSize=10000)

    	self.requiredStateTicks = 0
    	self.currentI = 0

    	self.sendState = SendState.IDLE

    	self.jammingPacket = None

    	# P-Persistent or Non-Persistent Characteristics
    	self.shouldSenseWait = shouldSenseWait
    	self.pPersistentProbability = pPersistentProbability


    def registerTick(self, currTime):

        generatePacketForTick(currTime)
    	sendPacketForTick(currTime)
    	receivePacketForTick(currTime)

    	
    def generatePacketForTick(self, currTime):
        self.sendQueue.registerTick(currTime)


    def sendPacketForTick(self, currTime):

    	if not self.sendQueue.isEmpty():
    		if self.sendState is SendState.IDLE:
    			self.sendState = SendState.SENSING
    			self.requiredStateTicks = self.requiredSensingTicks()

    		elif self.sendState is SendState.SENSING:
    			if self.requiredStateTicks <= 0:
    				self.sendState = SendState.PRESENDING
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
	    			self.sendState = SendState.IDLE

	    	elif self.sendState is SendState.PRESENDING:

	    		shouldSend = random.uniform(0, 1) <= self.pPersistentProbability
	    		if shouldSend:
	    			self.sendState = SendState.SENDING
	    		else:
	    			self.sendState = SendState.PRESENDWAITING
	    			waitTicks = self.generateRandomWaitTicks(currentI)
	    			self.requiredStateTicks = waitTicks

	    	elif self.sendState is SendState.PRESENDWAITING:
	    		if self.requiredStateTicks > 0:
	    			self.requiredStateTicks -= 1
	    		else:
	    			self.sendState = SendState.WAITING

    		elif self.sendState is SendState.SENDING:

    			# 0- sending still, 1: success, -1: collision
    			status = self.sendPacketForTick(currTime)
    			if status == SendStatus.SENDING:
    				pass
    			elif status == SendStatus.SUCCESS:
    				self.sendState = SendState.IDLE
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
	    			self.sendState = SendState.IDLE
    	else:
    		pass # no packet to send


    def receivePacketForTick(self, currTime):
    	packet = self.csmaBus.packetArrivedForNode(self)

    	if packet is not None:
            packet.completeService(currTime + packet.packetLength / self.lanSpeed)
    		self.csmaBus.removePacket(packet.uid)


    # returns True if the medium is busy, vice versa
    def senseMediumBusy(self, currTime):
    	return self.csmaBus.isBusyForNode(self, currTime)

    def sendPacketForTick(self, currentTime):

    	self.requiredStateTicks = requiredSendingTicks()
    	if senseMediumBusy(currentTime):
    		status = SendStatus.COLLISION
    	elif self.requiredStateTicks > 0:
    		self.requiredStateTicks -= 1
    		status = SendStatus.SENDING

    		if self.requiredStateTicks == self.requiredSendingTicks():
    			newPacket = generateNewPacket(currentTime)
                newPacket.startService(currentTime)
    			self.csmaBus.addPacket(newPacket)

    	elif self.requiredStateTicks <= 0:
			status = SendStatus.SUCCESS

    	return status

    def generateNewPacket(self, currentTime):
    	destNodeIndex = random.randint(1, self.lan.numNodes)
    	while destNodeIndex == self.index:
    		destNodeIndex = random.randint(1, self.lan.numNodes)

    	newPacket = CSMAPacket(self.packetLength, currentTime, self.index, destNodeIndex)
    	return newPacket



class LAN:

    def __init__(self, totalTicks, N, A, shouldSenseWait, P=1, W=10**6, L=1500*8):
        self.totalTicks = totalTicks
        self.N = N
        self.A = A
        self.P = P
        self.csmaBus = CSMABus()
        self.stats = Statistics()

        self.nodes = []
        for index in xrange(0, self.N):
            node = NodeNonAndPPersistent(index, W, L, self.csmaBus, shouldSenseWait, self.P)
            self.nodes.append(node)

    def simulate(self):
        for tick in xrange(0, self.totalTicks):
            for nodeIndex in xrange(1, self.N):
                currTime = getCurrentTime(tick)
                self.nodes[nodeIndex].registerTick(currTime)


        results = "blah"
        results2 = "blah"
        return (results, results2)

    def getCurrentTime(self, tickCount):
        return tickCount * kSecondsPerTick

class Statistics:

    def __init__(self):

    def trackPacketServiced(self, packet)


def main(args):
	
    simulationTime = 5 * 60
    totalTicks = simulationTime / kSecondsPerTick

    Ns = [20, 40 ,60, 80, 100]
    As = [6, 20]

    for A in As:
        for N in Ns:
            myLAN = LAN(totalTicks, N, A, True)
            (results, results2) = myLAN.simulate()


    print("results")


if __name__ == "__main__":
	main(sys.argv[1:])


 

 

