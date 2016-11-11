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

    # Constants
    experimentRepeats = kNumRepeats
    secondsPerTick = kSecondsPerTick

    def __init__(self, packetPerSecond, length, queueSize=10000):

        self.packetsPerSecond = packetPerSecond
        self.packetLength = length
        self.maxQueueSize = queueSize

        self.queue = Queue.Queue(maxsize=self.maxQueueSize)
        packGen = PacketGenerator(self.packetsPerSecond, self.secondsPerTick, self.packetLength)


    # Returns bool
    def isEmpty(self):
        return self.queue.empty()

    def registerTick(self, currentTime):

        # Generation
        generatedPacket = packGen.registerTick(currentTime)

        if generatedPacket is not None:
            newPacket = generatedPacket
            # totalCreatedPackets += 1

            if not self.queue.full():
                self.queue.put(newPacket)
            else:
                # queue full, drop packet
                pass
                # totalDroppedPackets += 1


class PacketGenerator:
    packetsPerSecond = 5
    _secondsPerTick = 0
    packetLength = 200

    uniformRandomVariable = 1.0

    currentTickerCount = 0
    requiredTickerCount = 1000

    # param packetLength in bits
    def __init__(self, packetPerSecond, secondsPerTick, packetLength):
        self.packetsPerSecond = packetPerSecond
        self._secondsPerTick = secondsPerTick
        self.packetLength = packetLength
        self.startNewPacket()

    def startNewPacket(self):
        uniformRandomVariable = random.uniform(0, 1)
        timeRequired = (-1.0 / self.packetsPerSecond) * math.log(1.0 - uniformRandomVariable)
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
            return Packet(self.packetLength, currentTime)
        else:
            return None




