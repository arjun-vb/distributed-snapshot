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
c2c_connections = {}
outgoing = []
incoming = []
currentBalance = 10



snapBalance = 0
clientStates = []

class Connections(Thread):
	def __init__(self,connection):
		Thread.__init__(self)
		self.connection = connection

	def run(self):
		while True:
			response = self.connection.recv(buff_size)
			data = pickle.loads(response)

			if(data.reqType == "TRANSACTION"):
				currentBalance += data.amount
				print("Updated Balance is " + currentBalance)
			elif(data.reqType == ""):



class MarkerThread(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.connection = connection

	def run(self):
		while True:
			if()

def sleep():
	time.sleep(3)

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
			new_client= Connections(connection)
			new_client.start()
			c2c_connections[i] = new_client
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
			c2c_connections[i] = new_client
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
			c2c_connections[i] = new_client
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

		c2c_connections[2] = client2client
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

		c2c_connections[3] = client2client
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

		c2c_connections[4] = client2client
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

