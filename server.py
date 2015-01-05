#!/usr/bin/env python
import Queue # Import queue module
import socket # Import socket module
import threading # Import threading module

class Server:
	serverSocket = socket.socket() # Create a socket object
	host = socket.gethostname() # Get local machine name
	port = 12345 # Reserve a port for your service.
	threadCounter = 0

	def start(self):
		self.serverSocket.bind((self.host, self.port)) # Bind to the port
		self.serverSocket.listen(1000) # Now wait for client connection.
		print('Server socket is created and it is the listening mode')
		while True:
			connection, address = self.serverSocket.accept() # Establish connection with client.
			print('Got connection from ', address)
			self.threadCounter = self.threadCounter + 1
			cThread = clientThread(self.threadCounter, "Thread-" + str(self.threadCounter), connection, address)
			cThread.start()

class clientThread(threading.Thread):
	
	def __init__(self, threadID, name, connection, address):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.connection = connection
		self.address = address
		self.queueLock = threading.Lock()
		self.state = "Connectionless"
	
	def run(self):
		print("Starting thread " + str(self.threadID) + " " + self.name + " " + str(self.address))
		# Wait for client's requests, read and answer them
		while True:
			request = self.connection.recv(1024).strip()
			response = self.parser(request)
			self.connection.send(response)
		self.connection.close()

	def parser(self, request):
		print("Incoming request : " + request)
		if request:
			requestParsed = request.split("#")
			if requestParsed[0] == "CONN":
				response = "CONR"
				username = requestParsed[1] if len(requestParsed) > 1 else None
				if username:
					if not activeUsers.get(username, None):
						self.state = "Connected"
						activeUsers[username] = self.connection
						response += "#Success#Welcome to SWE544 backgammon"
					else:
						response += "#Busy#The username you chosed is in use, please choose another"
				else: 
					response = "WRRE#Fail#Your request is not valid"
			else: 
				response = "WRRE#Fail#Your request is not valid"
		else: 
			response = "WRRE#Fail#Your request is not valid"
		return response

# Queues
readyToPlayQueue = Queue.Queue(10)
readyToWatchQueue = Queue.Queue(1000)

# ActiveUsers
activeUsers = dict()

server = Server()
server.start()