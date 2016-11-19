from lab2_queue_for_lab2 import Packet
from lab2_queue_for_lab2 import PacketGenerator
from lab2_queue_for_lab2 import PacketQueue
import uuid
import sys
import random

# Carrier Sense Multiple Access with collision detection(CSMA/CD)

kSecondsPerTick = 10**(-5) # should be 10**(-8)
kSenseBitTimes = 96
kJammingBitTimes = 48
kBEBMaxI = 10


class CSMAPacket(Packet):

    def __init__(self, length, time, srcNodeIndex, destNodeIndex):
        super(CSMAPacket, self).__init__(length, time)
        self.srcNodeIndex = srcNodeIndex
        self.destNodeIndex = destNodeIndex
        self.uid = uuid.uuid4()


class CSMABus(object):

    # S === propSpeed
    def __init__(self, nodeDistance=10, propSpeed=2*(10**8), lanSpeed=10**6):
        self.packets = {}
        self.nodeDistance = nodeDistance
        self.propSpeed = propSpeed
        self.lanSpeed = lanSpeed

    def physicalDist(self, nodeIndex1, nodeIndex2):
        phyDist = abs(nodeIndex1 - nodeIndex2) * self.nodeDistance
        return float(phyDist)

    # Assuming nodes are linearly arranged on a bus, 
    # node is sequencially index from 1 to N from left to right
    def isBusyForNode(self, nodeIndex, currTime):
        isBusy = False
        for key, packet in self.packets.iteritems():
            physicalDist = self.physicalDist(nodeIndex, packet.srcNodeIndex)
            firstPassTime = physicalDist / self.propSpeed + packet.creationTime
            lastPassTime = firstPassTime + packet.packetLength / float(self.lanSpeed)

            if firstPassTime <= currTime <= lastPassTime:
                isBusy = True

        return isBusy

    # self, CSMAPacket
    def addPacket(self, packet):
        # print("Adding Packet\n")
        self.packets[packet.uid] = packet

    def removePacket(self, packetUid):
        # print("Removing Packet\n")
        pkt = self.packets[packetUid]
        del self.packets[packetUid]
        return pkt

    # node: Integer
    def packetArrivedForNode(self, nodeIndex, currTime):

        if nodeIndex <=0:
            print("Error: Node index cannot be zero or negative!")
            return None

        for key, packet in self.packets.iteritems():
            if packet.destNodeIndex == nodeIndex:
                
                physicalDist = self.physicalDist(packet.destNodeIndex, packet.srcNodeIndex)
                firstPassTime = physicalDist / float(self.propSpeed) + packet.creationTime
                lastPassTime = firstPassTime + packet.packetLength / float(self.lanSpeed)

                # see if the packet has been fully processed
                if lastPassTime >= currTime:
                    return packet
        return None


class Node(object):

    def __init__(self, lanSpeed, index, L):
        self.index = index
        self.lanSpeed = lanSpeed
        self.packetLength = L #L Packet Length (bits)[fixed]

    # iVal is an integer
    # Returns number of ticks required for the wait
    def generateRandomWaitTicks(self, iVal):
        if iVal >10:
            print("Error: BEB i value should be less or equal to 10\n")
            return None

        randVal = random.randint(0, 2**iVal - 1)
        Tp = 512 / self.lanSpeed
        randTime = Tp * randVal
        ticksReq = randTime / kSecondsPerTick
        return ticksReq

    def requiredSensingTicks(self):
        ticks = float(kSenseBitTimes)/float(self.lanSpeed)/kSecondsPerTick
        return round(ticks)

    def requiredJammingTicks(self):
        ticks = float(kJammingBitTimes)/self.lanSpeed/kSecondsPerTick
        return round(ticks)

    def requiredSendingTicks(self):
        ticks = float(self.packetLength)/self.lanSpeed/kSecondsPerTick
        return round(ticks)


class SendState(object):
    IDLE = 0
    SENSING = 1
    WAITING = 2
    PRESENDING = 3
    PRESENDWAITING = 4
    SENDING = 5
    JAMMING = 6
    POSTJAMMING = 7 #exponential backoff
    
class SendStatus(object):
    SENDING = 0
    SUCCESS = 1
    COLLISION = -1


class NodeNonAndPPersistent(Node):

    def __init__(self, index, numNodes, A, W, L, csmaBus, shouldSenseWait, pPersistentProbability):
        super(NodeNonAndPPersistent, self).__init__(W, index, L)
        self.numNodes = numNodes

        self.avgArrival = A #A Average arrival rate (pkts/s)[var]

        self.csmaBus = csmaBus
        self.sendQueue = PacketQueue(self.avgArrival, L, queueSize=1000, secondsPerTick=kSecondsPerTick)
        self.statistics = Statistics.sharedStatistics()

        self.requiredStateTicks = 0
        self.currentI = 0

        self.sendState = SendState.IDLE

        self.jammingPacket = None

        # P-Persistent or Non-Persistent Characteristics
        self.shouldSenseWait = shouldSenseWait
        self.pPersistentProbability = pPersistentProbability


    def registerTick(self, currTime):

        self.generatePacketForTick(currTime)
        self.generalSendPacketForTick(currTime)
        self.receivePacketForTick(currTime)

        
    def generatePacketForTick(self, currTime):
        self.sendQueue.registerTick(currTime)


    def generalSendPacketForTick(self, currTime):

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
                    waitTicks = self.generateRandomWaitTicks(self.currentI)
                    if not self.shouldSenseWait:
                        waitTicks = 0

                    self.sendState = SendState.WAITING
                    self.requiredStateTicks = waitTicks
                else:  # not sensed busy yet
                    pass

            elif self.sendState is SendState.WAITING:
                if self.requiredStateTicks > 0:
                    self.requiredStateTicks -= 1
                else: # Finish waiting
                    self.sendState = SendState.IDLE

            elif self.sendState is SendState.PRESENDING:

                shouldSend = random.uniform(0, 1) <= self.pPersistentProbability
                if shouldSend:
                    self.requiredStateTicks = self.requiredSendingTicks()
                    self.sendState = SendState.SENDING
                else:
                    self.sendState = SendState.PRESENDWAITING
                    waitTicks = self.generateRandomWaitTicks(self.currentI)
                    self.requiredStateTicks = waitTicks

            elif self.sendState is SendState.PRESENDWAITING:
                if self.requiredStateTicks > 0:
                    self.requiredStateTicks -= 1

                elif self.senseMediumBusy(currTime):
                    self.currentI += 1
                    if self.currentI > kBEBMaxI:
                        self.currentI = 10
                    self.requiredStateTicks = self.generateRandomWaitTicks(self.currentI)

                    self.sendState = SendState.POSTJAMMING
                else:
                    pass


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
                    self.currentI += 1
                    if self.currentI > kBEBMaxI:
                        self.currentI = 10
                    self.requiredStateTicks = self.generateRandomWaitTicks(self.currentI)

                    self.sendState = SendState.POSTJAMMING
                    self.csmaBus.removePacket(self.jammingPacket.uid)
                    return

                self.requiredStateTicks -= 1
                

            elif self.sendState is SendState.POSTJAMMING:

                if self.requiredStateTicks > 0:
                    self.requiredStateTicks -= 1
                else:
                    self.sendState = SendState.IDLE
        else:
            pass # no packet to send


    def receivePacketForTick(self, currTime):
        packet = self.csmaBus.packetArrivedForNode(self.index, currTime)

        if packet is not None:
            packet.completeService(currTime + packet.packetLength / float(self.lanSpeed))
            self.csmaBus.removePacket(packet.uid)
            self.statistics.trackPacketServiced(packet)

    # returns True if the medium is busy, vice versa
    def senseMediumBusy(self, currTime):
        return self.csmaBus.isBusyForNode(self.index, currTime)

    def sendPacketForTick(self, currentTime):

        if self.senseMediumBusy(currentTime):
            status = SendStatus.COLLISION
        elif self.requiredStateTicks > 0:
            self.requiredStateTicks -= 1
            status = SendStatus.SENDING

        elif self.requiredStateTicks <= 0:
            newPacket = self.generateNewPacket(currentTime)
            newPacket.startService(currentTime)
            self.csmaBus.addPacket(newPacket)
            self.sendQueue.popPacket()

            status = SendStatus.SUCCESS

        return status

    def generateNewPacket(self, currentTime):
        destNodeIndex = random.randint(1, self.numNodes)
        while destNodeIndex == self.index:
            destNodeIndex = random.randint(1, self.numNodes)

        newPacket = CSMAPacket(self.packetLength, currentTime, self.index, destNodeIndex)
        return newPacket


class LAN(object):

    def __init__(self, totalTicks, N, A, shouldSenseWait, P=1, W=10**6, L=1500*8):
        self.totalTicks = totalTicks
        self.N = N #Nodes
        self.A = A #AvgArrival
        self.P = P
        self.csmaBus = CSMABus()
        self.statistics = Statistics.sharedStatistics()

        self.nodes = []
        for index in xrange(0, self.N):
            node = NodeNonAndPPersistent(index, self.N, A, W, L, self.csmaBus, shouldSenseWait, self.P)
            self.nodes.append(node)

    def simulate(self):
        for tick in xrange(0, self.totalTicks):
            for nodeIndex in xrange(1, self.N):
                currTime = self.getCurrentTime(tick)
                self.nodes[nodeIndex].registerTick(currTime)

        endTime = self.getCurrentTime(self.totalTicks-1)
        throughput = self.statistics.networkThroughput(endTime)
        avgDelay = self.statistics.networkAverageDelay()
        return (throughput, avgDelay)

    def getCurrentTime(self, tickCount):
        return tickCount * kSecondsPerTick


_sharedStats = None
class Statistics(object):

    @classmethod
    def sharedStatistics(cls):
        global _sharedStats
        if _sharedStats is None:
            _sharedStats = cls()
        return _sharedStats

    def __init__(self, packetLength=1500*8, currTime=0):
        self.packetsReceived = 0
        self.packetLength = packetLength
        self.startTime = currTime
        self.packetDelaySum = 0.0

    def trackPacketServiced(self, packet):
        self.packetsReceived += 1
        self.packetDelaySum += packet.duration()

    def networkThroughput(self, currTime):
        totalDuration = currTime - self.startTime
        throughput = self.packetsReceived * self.packetLength / totalDuration
        return throughput

    def networkAverageDelay(self):
        if self.packetsReceived <= 0:
            print("Error: networkAverageDelay packetsReceived is zero")
            return 0
        avgDelay = float(self.packetDelaySum) / float(self.packetsReceived)
        return avgDelay

def simulateOnePersistent(totalTicks):
    Ns = [20, 40, 60, 80, 100]
    As = [6, 20]

    for A in As:
        for N in Ns:
            myLAN = LAN(totalTicks, N, A, False)
            (throughput, avgDelay) = myLAN.simulate()
            print("N[%d], A[%d], throughput[%.3fMbps], avgDelay[%fs]" % (N, A, throughput / 10 ** 6, avgDelay))

def simulateNonPersistent(totalTicks):

    Ns = [20, 40, 60, 80, 100]
    As = [6, 20]

    for A in As:
        for N in Ns:
            myLAN = LAN(totalTicks, N, A, True)
            (throughput, avgDelay) = myLAN.simulate()
            print("N[%d], A[%d], throughput[%.3fMbps], avgDelay[%fs]" % (N, A, throughput / 10 ** 6, avgDelay))


def simulatePPersistent(totalTicks):
    Ps = [0.01, 0.1, 1]
    As = [2, 4, 6, 8, 10]
    N = 30

    for P in Ps:
        for A in As:
            myLAN = LAN(totalTicks, N, A, False, P)
            (throughput, avgDelay) = myLAN.simulate()
            print("P[%.2f], A[%d], throughput[%.3fMbps], avgDelay[%fs]" % (P, A, throughput / 10 ** 6, avgDelay))


def main(args):
    
    simulationTime = 1.0
    totalTicks = int(simulationTime / kSecondsPerTick)

    print("Results\n")
    simulatePPersistent(totalTicks)
    simulateNonPersistent(totalTicks)

if __name__ == "__main__":
    main(sys.argv[1:])


 

 

