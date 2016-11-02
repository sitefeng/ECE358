import lab1_queue


# Carrier Sense Multiple Access with collision detection(CSMA/CD)

class LAN:
	def __init__(self):
		N = 0 #Number of computers [var]
		W = 0 #Speed of the LAN (bits/s)[fixed]
		avgArrival = 0 #Average arrival rate (pkts/s)[var]
		packetLength = 0 #Packet Length (bits)[fixed]
		P = 0 #Persistent CSMA param

class Node:
	#Constants
	secondsPerTick = 0.01

	# Input Variables
	avgArrival = 0 #A Average arrival rate (pkts/s)[var]
	packetLength = 0 #L Packet Length (bits)[fixed]


class NodeNonPersistent(Node):

    def __init__(self):
    	self.avgArrival = 0 #A Average arrival rate (pkts/s)[var]
    	self.packetLength = 0

    def registerTick(self):
		generator = PacketGenerator(self.avgArrival, self.secondsPerTick, self.packetLength)

    
    








