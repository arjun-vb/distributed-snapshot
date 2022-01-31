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
listenToChannel = False

c2c_connections = {}
outgoing = []
incoming = []

currentBalance = 10

clientStates = []

tempMessages = []
tempA = []
tempB = []
tempC = []
tempD = []
#tempMessages.append(tempA).append(tempB).append(tempC).append(tempD)

count = 0

recievedSnapshotCount = 0

markersInProgress = {}

snapBalance = {}

class Connections(Thread):
	def __init__(self,connection):
		Thread.__init__(self)
		self.connection = connection

	def run(self):

		while True:
			response = self.connection.recv(buff_size)
			data = pickle.loads(response)

			if(data.reqType == "TRANSACTION"):
				print("Recieved transaction message")
				for markerId in markersInProgress:
					if(markersInProgress[markerId].listenToChannel[data.fromClient] == True):
						markersInProgress[markerId].channelMessages[data.fromClient].append(data)

				currentBalance += data.amount
				print("Updated Balance is " + currentBalance)
			elif(data.reqType == "MARKER"):
				print("Recieved Marker message from " + str(data.fromClient))
				if(data.markerId in markersInProgress):
					if(markersInProgress[data.markerId].listenToChannel[data.fromClient] == True):
						markersInProgress[data.markerId].listenToChannel[data.fromClient] = False
						markersInProgress[data.markerId].recievedMarkers.append(data.fromClient)
						print("Recieved markers: ")
						for i in markersInProgress[data.markerId].recievedMarkers:
							print(i)

						initiator = int(data.markerId.split("|")[0])
						if(markersInProgress[data.markerId].recievedMarkers == incoming and initiator != pid):
							print("Sending snap to " + str(initiator))
							locState = State("SNAP", snapBalance[data.markerId], 
								markersInProgress[data.markerId].channelMessages)
							initiator = int(data.markerId.split("|")[0])
							c2c_connections[initiator].send(pickle.dumps(locState))
				else:
					sendMarkers(data.markerId, data.fromClient)
			elif(data.reqType == "SNAP"):
				print("Printing snap")


class MarkerThread(Thread):
	def __init__(self, markerId):
		Thread.__init__(self)
		self.markerId = markerId

	def run(self):
		global currentBalance

		sleep()
		snapBalance[self.markerId] = currentBalance
		
		for i in outgoing:
			message = Messages("MARKER", pid, self.markerId)
			print("Sending marker to "+ str(i))
			c2c_connections[i].send(pickle.dumps(message))


def sleep():
	time.sleep(0)

def sendMarkers(markerId, fromClient):
	
	markerThread = MarkerThread(markerId)
	markerThread.start()

	trackChannels = TrackChannels(markerId)

	markersInProgress[markerId] = trackChannels

	for i in incoming:
		if(i != fromClient):
			trackChannels.listenToChannel[i] = True
		else:
			markersInProgress[markerId].recievedMarkers.append(fromClient)

def incrementMarker():
	global count
	count = count + 1
	return str(pid) + "|" + str(count)

def main():
	ip = '127.0.0.1'
	client_port = 0
	global pid

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


	while True:
		print("=======================================================")
		print("| For Balance type 'BAL'                              |")
		print("| For transferring money - RECV_ID AMOUNT Eg.(2 5)    |")
		print("| For Snapshot type 'SNAP'                            |")
		print("=======================================================")
		user_input = raw_input()
		if (user_input == "BAL"):
			print("Balance is " + currentBalance)
		elif (user_input == "SNAP"):
			print("Initiating snapshot")
			markerId = incrementMarker()
			sendMarkers(markerId, pid)
		else:
			reciever, amount = user_input.split()
			if(amount < currentBalance):
				print("Insufficient Balance")
			else:
				currentBalance -= amount
				message = Messages("TRANSACTION", pid, "", amount)
				sleep()
				c2c_connections[reciever].send(pickle.dumps(message))


	closeSockets()

if __name__ == "__main__":
    main()

