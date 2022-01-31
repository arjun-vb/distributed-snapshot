import sys
import socket
import pickle
import heapq
import hashlib
import time

from threading import Thread
from common import *

buff_size = 1024
pid = 0
temp = 0

c2c_connections = {}
outgoing = []
incoming = []

currentBalance = 10

#clientStates = []
#tempMessages = []
#tempA = []
#tempB = []
#tempC = []
#tempD = []
#tempMessages.append(tempA).append(tempB).append(tempC).append(tempD)
#recievedSnapshotCount = 0
#snapbalance = {}

count = 0
markersInProgress = {}

class Connections(Thread):
	def __init__(self,connection):
		Thread.__init__(self)
		self.connection = connection

	def run(self):
		global currentBalance
		while True:
			response = self.connection.recv(buff_size)
			data = pickle.loads(response)

			if data.reqType == "TRANSACTION":
				print("Recieved transaction message")
				for markerId in markersInProgress:
					if(markersInProgress[markerId].listenToChannel[data.fromClient] == True):
						markersInProgress[markerId].channelMessages[data.fromClient].append(data.amount)

				currentBalance += int(data.amount)
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
		if markersInProgress[data.markerId].recievedMarkers == incoming and initiator != pid:
			print("Sending snap to " + str(initiator))
			channelState = {}
			for i in incoming:
				channelState[i] = markersInProgress[data.markerId].channelMessages[i]
			locState = State("SNAP", pid, data.markerId, markersInProgress[data.markerId].snapbalance, 
				channelState)
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
		initiator = int(markerId.split("|")[0])
		print("State of A:")		
		if initiator == 1:
			print("Balance of A: " + str(markersInProgress[markerId].snapbalance))
			print("Channel states: ")
			for i in incoming:
				print(str(i) + " : " + str(markersInProgress[markerId].channelMessages[i]))
		else:
			print("Balance of A: " + str(markersInProgress[markerId].recievedSnaps[1].localState))
			print("Channel states: ")
			for i in markersInProgress[markerId].recievedSnaps[1].channelState:
				print(str(i) + " : " + str(markersInProgress[markerId].recievedSnaps[1].channelState[i]))
		
		print("State of B:")
		if initiator == 2:
			print("Balance of B: " + str(markersInProgress[markerId].snapbalance))
			print("Channel states: ")
			for i in incoming:
				print(str(i) + " : " + str(markersInProgress[markerId].channelMessages[i]))
		else:
			print("Balance of B: " + str(markersInProgress[markerId].recievedSnaps[2].localState))
			print("Channel states: ")
			for i in markersInProgress[markerId].recievedSnaps[2].channelState:
				print(str(i) + " : " + str(markersInProgress[markerId].recievedSnaps[2].channelState[i]))
		
		print("State of C:")
		if initiator == 3:
			print("Balance of C: " + str(markersInProgress[markerId].snapbalance))
			print("Channel states: ")
			for i in incoming:
				print(str(i) + " : " + str(markersInProgress[markerId].channelMessages[i]))
		else:
			print("Balance of C: " + str(markersInProgress[markerId].recievedSnaps[3].localState))
			print("Channel states: ")
			for i in markersInProgress[markerId].recievedSnaps[3].channelState:
				print(str(i) + " : " + str(markersInProgress[markerId].recievedSnaps[3].channelState[i]))
		
		print("State of D:")
		if initiator == 4:
			print("Balance of D: " + str(markersInProgress[markerId].snapbalance))
			print("Channel states: ")
			for i in incoming:
				print(str(i) + " : " + str(markersInProgress[markerId].channelMessages[i]))
		else:
			print("Balance of D: " + str(markersInProgress[markerId].recievedSnaps[4].localState))
			print("Channel states: ")
			for i in markersInProgress[markerId].recievedSnaps[4].channelState:
				print(str(i) + " : " + str(markersInProgress[markerId].recievedSnaps[4].channelState[i]))


class MarkerThread(Thread):
	def __init__(self, markerId):
		Thread.__init__(self)
		self.markerId = markerId

	def run(self):
		global currentBalance

		sleep()
		markersInProgress[self.markerId].snapbalance = currentBalance
		#snapbalance[self.markerId] = currentBalance
		
		for i in outgoing:
			message = Messages("MARKER", pid, self.markerId)
			print("Sending marker to "+ str(i))
			c2c_connections[i].send(pickle.dumps(message))


def sleep():
	time.sleep(1)

def sendMarkers(markerId, fromClient):
	
	trackChannels = TrackChannels(markerId)

	markersInProgress[markerId] = trackChannels
	print("Marker ID is "  + str(markerId))
	markerThread = MarkerThread(markerId)
	markerThread.start()

	for i in incoming:
		if i != fromClient:
			markersInProgress[markerId].listenToChannel[i] = True
		else:
			markersInProgress[markerId].recievedMarkers.append(fromClient)

def incrementMarker():
	global count
	count += 1
	return str(pid) + "|" + str(count)

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
			new_client = Connections(connection)
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
		new_connection = Connections(client2client)
		new_connection.start()

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, client_port))
		client2client.listen(5)


		i = 3
		while i <= 4:
			connection, client_address = client2client.accept()
			print('Connected to: ' + client_address[0] + ':' + str(client_address[1]))
			new_client= Connections(connection)
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
		new_connection = Connections(client2client)
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
		new_connection = Connections(client2client)
		new_connection.start()

		client2client = socket.socket()
		client2client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		client2client.bind((ip, client_port))
		client2client.listen(2)


		i = 4
		while i <= 4:
			connection, client_address = client2client.accept()
			print('Connected to: ' + client_address[0] + ':' + str(client_address[1]))
			new_client= Connections(connection)
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
		new_connection = Connections(client2client)
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
		new_connection = Connections(client2client)
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
		new_connection = Connections(client2client)
		new_connection.start()

		incoming.append(2)
		outgoing.append(1)
		outgoing.append(2)
		outgoing.append(3)

	incoming.sort()
	outgoing.sort()

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
			if int(amount) > currentBalance:
				print("Insufficient Balance")
			else:
				currentBalance -= int(amount)
				message = Messages("TRANSACTION", pid, "", amount)
				sleep()
				c2c_connections[int(reciever)].send(pickle.dumps(message))


	closeSockets()

if __name__ == "__main__":
    main()
