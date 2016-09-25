import random
import math
import Queue


class Packet:
	packetLength = 0
	creationTime = -1

	servicedTime = -1
	serviced = False

	def __init__(self, length, time):
		self.packetLength = length
		self.creationTime = time
		self.serviced = False

	def service(self, time):
		self.servicedTime = time
		self.serviced = True

	def duration(self):
		if self.serviced == False or self.servicedTime == -1 or self.creationTime == -1:
			print "Not serviced yet"
			return -1

		return self.servicedTime - self.creationTime


class PacketQueue:

	# Inputs
	_packetsPerSecond = 5 # packets per second
	_packetLength = 200 # length
	_serviceTime = 0.01 # service time
	_queueUtilization = 0
	_totalTicks = 1000
	_maxQueueSize = 200
	
	# Constants
	experimentRepeats = 5
	secondsPerTick = 0.01
	

	def __init__(self, ticks, packetPerSecond, length, serviceTime, queueSize):
		self._totalTicks = ticks
		self._packetsPerSecond = packetPerSecond
		self._packetLength = length
		self._serviceTime = serviceTime
		self._queueUtilization = length * packetPerSecond / serviceTime # queue utilization
		self._maxQueueSize = queueSize


	# Returns EN, ET, PIdle, PLoss
	def simulateOnce(self):

		queue = Queue.Queue(maxsize = self._maxQueueSize)
		packGen = PacketGenerator(self._packetsPerSecond, self.secondsPerTick)
		packSer = PacketServer(self._serviceTime, self.secondsPerTick)

		numServiced = 0
		totalCumulativePackets = 0
		totalCreatedPackets = 0
		totalSojournTime = 0
		totalIdleTicks = 0
		totalDroppedPackets = 0

		for i in xrange(self._totalTicks):
			# Generation
			generated = packGen.registerTick()

			if generated:
				newPacket = Packet(self._packetLength, self.currentTime(i))
				totalCreatedPackets += 1

				if not queue.full():
					queue.put(newPacket)
				else:
					# queue full, drop packet
					totalDroppedPackets += 1

			# Servicing
			
			if packSer.statusBusy:
				maybePacket = packSer.registerTick()
				if maybePacket is not None:
					numServiced += 1
					totalSojournTime += maybePacket.duration()
				else:
					totalIdleTicks += 1

			else: # server not busy
				if queue.empty():
					pass
					#idle
				else:
					packet = queue.get()
					packSer.receiveNewPacket(packet)
					maybePacket = packSer.registerTick()
					if maybePacket is not None:
						numServiced += 1
						totalSojournTime += maybePacket.duration()

			# Statistics
			totalCumulativePackets += queue.qsize()


		if numServiced <=0 or self._totalTicks <=0 or totalCreatedPackets <=0:
			print "Error: cannot generate stats"
			return (-1, -1, -1, -1)

		# Average number of packets in queue
		currentEN = totalCumulativePackets / self._totalTicks

		# Average sojourn(packet duration) time 
		currentET = totalSojournTime / numServiced

		currentPIdle = totalIdleTicks / self._totalTicks

		currentPLoss = totalDroppedPackets / totalCreatedPackets


	# Returns average EN, ET, PIdle, PLoss
	def runSimulation(self):

		totalEN = 0
		totalET = 0
		totalPIdle = 0
		totalPLoss = 0

		for i in xrange(self.experimentRepeats):
			EN, ET, PIdle, PLoss = self.simulateOnce()

			totalEN += EN
			totalET += ET
			totalPIdle = PIdle
			totalPLoss = PLoss

		avgEN = totalEN / self.experimentRepeats
		avgET = totalET / self.experimentRepeats
		avgPIdle = totalPIdle / self.experimentRepeats
		avgPLoss = totalPLoss / self.experimentRepeats

		return (avgEN, avgET, avgPIdle, avgPLoss)


	# Convenience Functions
	def currentTime(self, tickCount):
		return tickCount * self.secondsPerTick




class PacketServer:
	
	statusBusy = False

	_serviceTime = 0.01
	_secondsPerTick = 0.1
	_packet = None

	currentTickerCount = 0
	requiredTickerCount = 1000

	def __init__(self, serviceTime, secondsPerTick):
		assert secondsPerTick > 0, "Each tick must have a positive time duration"

		self._serviceTime = serviceTime
		self._secondsPerTick = secondsPerTick
		self.statusBusy = False

	def receiveNewPacket(self, packet):
		self.requiredTickerCount = self._serviceTime / self._secondsPerTick
		self.currentTickerCount = 0
		self.statusBusy = True
		self._packet = packet

	# Returns packet if the current packet has been served
	def registerTick(self):
		self.currentTickerCount += 1

		if self.currentTickerCount >= self.requiredTickerCount:
			self.statusBusy = False
			return self._packet
		else:
			return None



class PacketGenerator:

	_packetsPerSecond = 5
	_secondsPerTick = 0

	uniformRandomVariable = 1.0

	currentTickerCount = 0
	requiredTickerCount = 1000


	def __init__(self, packetPerSecond, secondsPerTick):
		self._packetsPerSecond = packetPerSecond
		self._secondsPerTick = secondsPerTick
		self.startNewPacket()


	def startNewPacket(self):
		uniformRandomVariable = random.uniform(0, 1)
		timeRequired = (-1/self._packetsPerSecond) * math.log(1-uniformRandomVariable)
		self.requiredTickerCount = int(timeRequired / self._secondsPerTick)
		print "New Packet, requiredTickerCount: %d" % self.requiredTickerCount

		# Reset
		self.currentTickerCount = 0


	# Returns PacketArrived:Bool, indicating if the packet has arrived or not
	def registerTick(self):
		self.currentTickerCount += 1

		if self.currentTickerCount >= self.requiredTickerCount:
			print "Packet Generated"
			self.startNewPacket()
			return True
		else:
			return False



class InfiniteQueue(PacketQueue):
	def __init__(self, ticks, packetPerSecond, length, serviceTime):
		super.__init__(self, ticks, packetPerSecond, length, serviceTime, 100000000)



if __name__ == "__main__":
	queue = PacketQueue(100, 5, 200, 0.01, 200)
	EN, ET, PIdle, PLoss = queue.simulateOnce()

	print("EN, ET, PIdle, PLoss: %f, %f, %f, %f" % (EN, ET, PIdle, PLoss))


