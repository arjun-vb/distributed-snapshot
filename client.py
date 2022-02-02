import sys
import socket
import pickle
import time
import threading
from threading import Thread
from common import *

buff_size = 1024
pid = 0
temp = 0

c2c_connections = {}
outgoing = []
incoming = []

currentBalance = 10

markerCount = 0
markersInProgress = {}

myQueue = []
myQueueLock = threading.RLock()
balanceLock = threading.RLock()

class MasterHandler(Thread):
	def __init__(self):
		Thread.__init__(self)

	def run(self):
		global currentBalance
		while True:
			if len(myQueue) != 0:
				myQueueLock.acquire()
				data = myQueue.pop(0)
				myQueueLock.release()
				if data.reqType == "TRANSACTION":
					print("Recieved transaction message")
					for markerId in markersInProgress:
						if(markersInProgress[markerId].listenToChannel[data.fromClient] == True):
							markersInProgress[markerId].channelMessages[data.fromClient].append(data.amount)
					balanceLock.acquire()
					currentBalance += int(data.amount)
					balanceLock.release()
					print("Updated Balance is " + str(currentBalance))
				elif data.reqType == "MARKER":
					print("Recieved Marker message from " + str(data.fromClient))
					if data.markerId in markersInProgress:
						if markersInProgress[data.markerId].listenToChannel[data.fromClient] == True:
							markersInProgress[data.markerId].listenToChannel[data.fromClient] = False
							print(" Appending recieved markers : " + str(data.fromClient))
							markersInProgress[data.markerId].recievedMarkers.append(data.fromClient)
							self.handleRecievedMarkers(data)
					else:
						sendMarkers(data.markerId, data.fromClient)
						self.handleRecievedMarkers(data)

				elif data.reqType == "SNAP":
					print("Recieved snap from " + str(data.fromClient))
					self.handleLocalSnaps(data)

	def handleRecievedMarkers(self, data):
		global temp
		print("Recieved markers: +"  +  str(temp))
		markersInProgress[data.markerId].recievedMarkers.sort()
		for i in markersInProgress[data.markerId].recievedMarkers:
			print(str(i) + " " + str(temp))
		print("Incoming: + " + str(temp))
		for i in incoming:
			print(i)

		temp += 1

		initiator = int(data.markerId.split("|")[0])
		print("Initiator: "+ str(initiator)+ " PID: " + str(pid))
		#print(markersInProgress[data.markerId].recievedMarkers == incoming)
		#print(initiator != pid)
		#markersInProgress[data.markerId].recievedMarkers.sort()
		if markersInProgress[data.markerId].recievedMarkers == incoming and initiator != pid:
			print("Sending snap to " + str(initiator))
			channelState = {}
			for i in incoming:
				channelState[i] = markersInProgress[data.markerId].channelMessages[i]
			locState = State("SNAP", pid, data.markerId, markersInProgress[data.markerId].snapbalance, 
				channelState)
			sleep()
			c2c_connections[initiator].send(pickle.dumps(locState))
			#markersInProgress.pop(data.markerId)
		elif markersInProgress[data.markerId].recievedMarkers == incoming and initiator == pid and markersInProgress[data.markerId].snapshotCount == 3:
			self.printGlobalSnap(data.markerId)
			#markersInProgress.pop(data.markerId)


	def handleLocalSnaps(self, data):
		markersInProgress[data.markerId].recievedSnaps[data.fromClient] = data
		markersInProgress[data.markerId].snapshotCount += 1
		markersInProgress[data.markerId].recievedMarkers.sort()
		if markersInProgress[data.markerId].snapshotCount == 3 and markersInProgress[data.markerId].recievedMarkers == incoming:
			self.printGlobalSnap(data.markerId)
			#markersInProgress.pop(data.markerId)

	def printGlobalSnap(self, markerId):

		#initiator = int(markerId.split("|")[0])
		print("=====================================================")
		for j in range(1,5):
			print("-------------------------------------------------")
			print("State of "+str(j)+": ")
			if j == pid:
				print("Balance of "+ str(j) +": " + str(markersInProgress[markerId].snapbalance))
				print("Channel states: ")
				for i in incoming:
					print(str(i) + " : " + str(markersInProgress[markerId].channelMessages[i]))
			else:
				print("Balance of "+ str(j) +": " + str(markersInProgress[markerId].recievedSnaps[j].localState))
				print("Channel states: ")
				for i in markersInProgress[markerId].recievedSnaps[j].channelState:
					print(str(i) + " : " + str(markersInProgress[markerId].recievedSnaps[j].channelState[i]))
		print("=====================================================")

		
class ClientConnections(Thread):
	def __init__(self,connection):
		Thread.__init__(self)
		self.connection = connection

	def run(self):
		
		while True:
			response = self.connection.recv(buff_size)
			data = pickle.loads(response)
			myQueueLock.acquire()
			myQueue.append(data)
			myQueueLock.release()


class MarkerThread(Thread):
	def __init__(self, markerId):
		Thread.__init__(self)
		self.markerId = markerId

	def run(self):
		global currentBalance
		
		sleep()
		#snapbalance[self.markerId] = currentBalance
		
		for i in outgoing:
			message = Messages("MARKER", pid, self.markerId)
			print("Sending marker to "+ str(i))
			c2c_connections[i].send(pickle.dumps(message))


def sleep():
	time.sleep(3)

def sendMarkers(markerId, fromClient):
	print("Marker ID is "  + str(markerId))

	trackChannels = TrackChannels(markerId)

	markersInProgress[markerId] = trackChannels
	markersInProgress[markerId].snapbalance = currentBalance
	
	markerThread = MarkerThread(markerId)
	markerThread.start()

	for i in incoming:
		if i != fromClient:
			markersInProgress[markerId].listenToChannel[i] = True
		else:
			markersInProgress[markerId].recievedMarkers.append(fromClient)

def incrementMarker():
	global markerCount
	markerCount += 1
	return str(pid) + "|" + str(markerCount)

def main():
	ip = '127.0.0.1'
	client_port = 0
	global pid
	global currentBalance

	if sys.argv[1] == "p1":
		client_port = 7001
		pid = 1
	elif sys.argv[1] == "p2":
		client_port = 7002
		pid = 2
	elif sys.argv[1] == "p3":
		client_port = 7003
		pid = 3
	elif sys.argv[1] == "p4":
		client_port = 7004
		pid = 4

	if client_port == 7001: 
		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, client_port))
		client2client.listen(5)
		print('Waiting for a Connection..')

		i = 2
		while i <= 4:
			connection, client_address = client2client.accept()
			print('Connected to: ' + client_address[0] + ':' + str(client_address[1]))
			new_client = ClientConnections(connection)
			new_client.start()
			c2c_connections[i] = connection
			i+=1
		incoming.append(2)
		incoming.append(4)
		outgoing.append(2)

	if client_port == 7002:
		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, 7021))
		
		try:
			client2client.connect((ip, 7001))
			print('Connected to: ' + ip + ':' + str(7001))
		except socket.error as e:
			print(str(e))

		c2c_connections[1] = client2client
		new_connection = ClientConnections(client2client)
		new_connection.start()

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, client_port))
		client2client.listen(5)


		i = 3
		while i <= 4:
			connection, client_address = client2client.accept()
			print('Connected to: ' + client_address[0] + ':' + str(client_address[1]))
			new_client= ClientConnections(connection)
			new_client.start()
			c2c_connections[i] = connection
			i+=1

		incoming.append(1)
		incoming.append(3)
		incoming.append(4)
		outgoing.append(1)
		outgoing.append(4)

	if client_port == 7003:

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, 7031))
		
		try:
			client2client.connect((ip, 7001))
			print('Connected to: ' + ip + ':' + str(7001))
		except socket.error as e:
			print(str(e))

		c2c_connections[1] = client2client
		new_connection = ClientConnections(client2client)
		new_connection.start()

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, 7032))
		
		try:
			client2client.connect((ip, 7002))
			print('Connected to: ' + ip + ':' + str(7002))
		except socket.error as e:
			print(str(e))

		c2c_connections[2] = client2client
		new_connection = ClientConnections(client2client)
		new_connection.start()

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, client_port))
		client2client.listen(2)


		i = 4
		while i <= 4:
			connection, client_address = client2client.accept()
			print('Connected to: ' + client_address[0] + ':' + str(client_address[1]))
			new_client= ClientConnections(connection)
			new_client.start()
			c2c_connections[i] = connection
			i+=1
		incoming.append(4)
		outgoing.append(2)

	if client_port == 7004:

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, 7041))
		
		try:
			client2client.connect((ip, 7001))
			print('Connected to: ' + ip + ':' + str(7001))
		except socket.error as e:
			print(str(e))

		c2c_connections[1] = client2client
		new_connection = ClientConnections(client2client)
		new_connection.start()

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, 7042))
		
		try:
			client2client.connect((ip, 7002))
			print('Connected to: ' + ip + ':' + str(7002))
		except socket.error as e:
			print(str(e))

		c2c_connections[2] = client2client
		new_connection = ClientConnections(client2client)
		new_connection.start()

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, 7043))
		
		try:
			client2client.connect((ip, 7003))
			print('Connected to: ' + ip + ':' + str(7003))
		except socket.error as e:
			print(str(e))

		c2c_connections[3] = client2client
		new_connection = ClientConnections(client2client)
		new_connection.start()

		incoming.append(2)
		outgoing.append(1)
		outgoing.append(2)
		outgoing.append(3)

	incoming.sort()
	outgoing.sort()

	masterHandler = MasterHandler()

	masterHandler.start()
	
	while True:
		print("=======================================================")
		print("| For Balance type 'BAL'                              |")
		print("| For transferring money - RECV_ID AMOUNT Eg.(2 5)    |")
		print("| For Snapshot type 'SNAP'                            |")
		print("=======================================================")
		user_input = raw_input()
		if user_input == "BAL":
			print("Balance is " + str(currentBalance))
		elif user_input == "SNAP":
			print("Initiating snapshot")
			markerId = incrementMarker()
			sendMarkers(markerId, pid)
		else:
			reciever, amount = user_input.split()
			if int(reciever) in outgoing:
				if int(amount) > currentBalance:
					print("Insufficient Balance")
				else:
					balanceLock.acquire()
					currentBalance -= int(amount)
					balanceLock.release()
					message = Messages("TRANSACTION", pid, "", amount)
					sleep()
					c2c_connections[int(reciever)].send(pickle.dumps(message))
					print("Updated Balance of " + str(pid)  + " is " + str(currentBalance))
			else:
				print("Client " + str(reciever) + " is not connected")


if __name__ == "__main__":
    main()
