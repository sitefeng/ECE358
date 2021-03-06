import random
import math
import Queue
import sys


kSecondsPerTick = 0.0001
kNumRepeats = 5

class Packet:

    # Note: since transmission information was not provided, startServiceSpeed is the
    # same as creationTime, give or take.

    def __init__(self, length, time):
        self.packetLength = length
        self.creationTime = time
        self.serviced = False
        self.servicedTime = -1
        self.startServiceSpeed = -1

    def completeService(self, time):
        self.servicedTime = time
        self.serviced = True

    def startService(self, time):
        self.startServiceSpeed = time

    def duration(self):
        if self.serviced == False or self.servicedTime == -1 or self.creationTime == -1:
            print "Not serviced yet"
            return -1

        return self.servicedTime - self.creationTime


class PacketQueue:
    # Inputs
    _packetsPerSecond = 5  # packets per second
    _packetLength = 200  # length
    _serviceSpeed = 10  # service time [Mbps]
    _totalTicks = 1000
    _maxQueueSize = 200

    # Constants
    experimentRepeats = kNumRepeats
    secondsPerTick = kSecondsPerTick

    def __init__(self, ticks, packetPerSecond, length, serviceSpeed, queueSize):
        self._totalTicks = ticks
        self._packetsPerSecond = packetPerSecond
        self._packetLength = length
        self._serviceSpeed = serviceSpeed
        self._maxQueueSize = queueSize

    # Returns EN, ET, PIdle, PLoss
    def simulateOnce(self):

        queue = Queue.Queue(maxsize=self._maxQueueSize)
        packGen = PacketGenerator(self._packetsPerSecond, self.secondsPerTick, self._packetLength)
        packSer = PacketServer(self._packetsPerSecond, self._serviceSpeed, self.secondsPerTick)

        numServiced = 0
        totalCumulativePackets = 0.0
        totalCreatedPackets = 0
        totalSojournTime = 0.0
        totalIdleTicks = 0
        totalDroppedPackets = 0

        currentTime = -1

        for i in xrange(self._totalTicks):
            currentTime = self.currentTime(i)

            # Generation
            generatedPacket = packGen.registerTick(currentTime)

            if generatedPacket is not None:
                newPacket = generatedPacket
                totalCreatedPackets += 1

                if not queue.full():
                    queue.put(newPacket)
                else:
                    # queue full, drop packet
                    totalDroppedPackets += 1

            ##############
            # Servicing
            if packSer.statusBusy:
                maybePacket = packSer.registerTick(currentTime)
                if maybePacket is not None:
                    numServiced += 1
                    totalSojournTime += maybePacket.duration()
                else:
                    pass
                    # Busy processing

            else:  # server not busy
                if queue.empty():
                    pass
                    # idle
                    totalIdleTicks += 1
                else:
                    packet = queue.get()
                    packSer.receiveNewPacket(packet, currentTime)
                    maybePacket = packSer.registerTick(currentTime)
                    if maybePacket is not None:
                        numServiced += 1
                        totalSojournTime += maybePacket.duration()

            # Statistics
            totalCumulativePackets += queue.qsize()

        if numServiced <= 0 or self._totalTicks <= 0 or totalCreatedPackets <= 0:
            print "No Packet Served"
            return (-1, -1, -1, -1)

        # Average number of packets in queue
        currentEN = float(totalCumulativePackets) / self._totalTicks

        # Average sojourn(packet duration) time 
        currentET = float(totalSojournTime) / numServiced

        currentPIdle = float(totalIdleTicks) / self._totalTicks

        currentPLoss = float(totalDroppedPackets) / totalCreatedPackets

        return (currentEN, currentET, currentPIdle, currentPLoss)

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

        avgEN = float(totalEN) / self.experimentRepeats
        avgET = float(totalET) / self.experimentRepeats
        avgPIdle = float(totalPIdle) / self.experimentRepeats
        avgPLoss = float(totalPLoss) / self.experimentRepeats

        return (avgEN, avgET, avgPIdle, avgPLoss)

    # Convenience Functions
    def currentTime(self, tickCount):
        return tickCount * self.secondsPerTick


class PacketServer:
    statusBusy = False

    _serviceSpeed = 0  # [Mbps]
    _secondsPerTick = 0
    _packetsPerSecond = 0
    _packet = None

    currentTickerCount = 0
    requiredTickerCount = 1000

    def __init__(self, packetsPerSecond, serviceSpeed, secondsPerTick):
        assert secondsPerTick > 0, "Each tick must have a positive time duration"

        self._serviceSpeed = serviceSpeed
        self._secondsPerTick = secondsPerTick
        self._packetsPerSecond = packetsPerSecond
        self.statusBusy = False

    def receiveNewPacket(self, packet, time):
        tickDuration = float(packet.packetLength) / (self._serviceSpeed * 10**6)
        self.requiredTickerCount = tickDuration / self._secondsPerTick
        self.currentTickerCount = 0
        self.statusBusy = True
        self._packet = packet
        self._packet.startService(time)

    # Returns packet if the current packet has been served
    def registerTick(self, time):
        self.currentTickerCount += 1

        if self.currentTickerCount >= self.requiredTickerCount:
            self.statusBusy = False
            self._packet.completeService(time)
            return self._packet
        else:
            return None


class PacketGenerator:
    _packetsPerSecond = 5
    _secondsPerTick = 0
    _packetLength = 200

    uniformRandomVariable = 1.0

    currentTickerCount = 0
    requiredTickerCount = 1000

    # param packetLength in bits
    def __init__(self, packetPerSecond, secondsPerTick, packetLength):
        self._packetsPerSecond = packetPerSecond
        self._secondsPerTick = secondsPerTick
        self._packetLength = packetLength
        self.startNewPacket()

    def startNewPacket(self):
        uniformRandomVariable = random.uniform(0, 1)
        timeRequired = (-1.0 / self._packetsPerSecond) * math.log(1.0 - uniformRandomVariable)
        self.requiredTickerCount = float(timeRequired) / float(self._secondsPerTick)
        # print "New Packet, requiredTickerCount: %d" % self.requiredTickerCount

        # Reset
        self.currentTickerCount = 0

    # Returns PacketArrived:Bool, indicating if the packet has arrived or not
    def registerTick(self, currentTime):
        self.currentTickerCount += 1

        if self.currentTickerCount >= self.requiredTickerCount:
            # print "Packet Generated"
            self.startNewPacket()
            return Packet(self._packetLength, currentTime)
        else:
            return None


class InfiniteQueue(PacketQueue):
    def __init__(self, ticks, packetPerSecond, length, serviceSpeed):
        super.__init__(self, ticks, packetPerSecond, length, serviceSpeed, 100000000)


def main(args):
    # TICKS, lambda, length, c, k

    numTicks = 50000
    packetsPerSecond = 250
    packetLength = 2000
    serviceSpeed = 1
    queueSize = 30

    if len(args) == 4 or len(args) == 5:
        numTicks = int(args[0])
        packetsPerSecond = int(args[1])
        packetLength = int(args[2])
        serviceSpeed = int(args[3])

    if len(args) == 4:
        queueSize = 1000000000
    elif len(args) == 5:
        queueSize = int(args[4])
    else:
        print("Warning: Number of input is incorrect, proceeding anyway...")

    # ticks, packetPerSecond, length, serviceSpeed, queueSize:
    queue = PacketQueue(numTicks, packetsPerSecond, packetLength, serviceSpeed, queueSize)
    EN, ET, PIdle, PLoss = queue.runSimulation()

    PIdle *= 100
    PLoss *= 100

    print(
        "\n EN - Average number of packets in queue - [%f packets]\n ET - Average sojourn time - [%f sec]\n PIdle - "
        "Percentage queue idle - [%f%%]\n PLoss - Percentage package loss - [%f%%]\n" % (EN, ET, PIdle, PLoss)
    )
    print("\n\n Note: Service Speed is in [Mbps] units. Eg: 2 [Mbps]")


def generateGraph():
    # TICKS, lambda, length, c, k

    numSeconds = 300
    numTicks = int(numSeconds / kSecondsPerTick)
    packetsPerSecond = -1
    packetLength = 2000
    serviceSpeed = 1
    queueSize = 100000000

    for _p in xrange(2, 10, 1):
        p = _p / 10.0
        packetsPerSecond = p * float(serviceSpeed * 10 ** 6) / float(packetLength)

        # ticks, packetPerSecond, length, serviceSpeed, queueSize:
        queue = PacketQueue(numTicks, packetsPerSecond, packetLength, serviceSpeed, queueSize)
        EN, ET, PIdle, PLoss = queue.runSimulation()

        PIdle *= 100
        PLoss *= 100

        print(
            "\n EN - Average number of packets in queue - [%f packets]\n ET - Average sojourn time - [%f sec]\n PIdle - "
            "Percentage queue idle - [%f%%]\n PLoss - Percentage package loss - [%f%%]\n" % (EN, ET, PIdle, PLoss)
        )


if __name__ == "__main__":
    # generateGraph()
    main(sys.argv[1:])
