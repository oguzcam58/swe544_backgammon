#!/usr/bin/env python
import Queue # Import queue module
import socket # Import socket module
import threading # Import threading module

# ------------------------Server------------------------
class Server:
	serverSocket = socket.socket() # Create a socket object
	host = socket.gethostname() # Get local machine name
	port = 12345 # Reserve a port for your service.
	

	def start(self):
		self.serverSocket.bind((self.host, self.port)) # Bind to the port
		self.serverSocket.listen(1000) # Now wait for client connection.
		print('Server socket is created and it is the listening mode on ' + self.host + ":" + str(self.port))
		while True:
			connection, address = self.serverSocket.accept() # Establish connection with client.
			print('Got connection from ', address)
			
			threadLock.acquire()
			threadCounter += 1
			cThread = clientThread(threadCounter, "Thread-" + str(threadCounter), connection, address)
			threadLock.release()
			
			cThread.start()

# ------------------------ClientThread------------------------
class clientThread(threading.Thread):
	
	def __init__(self, threadID, name, connection, address):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.connection = connection
		self.address = address
		self.registeredUsername = ""
		# Possible States	
		self.Connectionless = "Connectionless" # String Constant
		self.Connected = "Connected" # String Constant
		# Initial State
		self.state = self.Connectionless
	
	def run(self):
		print("Starting thread " + str(self.threadID) + " " + self.name + " " + str(self.address))
		# Wait for client's requests, read and answer them
		while True:
			request = self.connection.recv(1024).strip()
			response = self.parser(request)
			self.connection.send(response)
		self.connection.close()

	def parser(self, request):
		if debug:
			print("Incoming request : " + request) # Debug message
		response = notValidRequest
		if request:
			requestParsed = request.split("#")
			
			# Connectionless state, no record on active users
			if self.state == self.Connectionless:
				if debug:
					print("Checking on Connectionless state") # Debug message
				
				if requestParsed[0] == "CONN":
					response = "CONR"
					username = requestParsed[1] if len(requestParsed) > 1 else None
					if username:
						if len(username) > 20:
							response += "#Fail#Username can be 20 characters maximum"
						else:
							threadLock.acquire()
							if not activeUsers.get(username, None):
								activeUsers[username] = self.connection
								response += "#Success#Welcome to SWE544 backgammon"
								self.registeredUsername = username
								self.state = self.Connected
							else:
								response += "#Busy#There is an active user with " + username + " username, please choose another username"
							threadLock.release()
					else: 
						response = notValidRequest
				else: 
					response = notValidRequest

			# Connected state
			elif self.state == self.Connected:
				if debug:
					print("Checking on Connected state") # Debug message

				if requestParsed[0] == "NEWG":
					threadLock.acquire()
					if readyToPlayQueue.empty():
						readyToPlayQueue.put(self.registeredUsername)
						response = "NEGR#Wait#There is no one wants to play at the moment; you are added to waiting list"
					else:
						opponent = readyToPlayQueue.get()
						threadCounter += 1
						game = gameThread(threadCounter, "Thread-" + str(threadCounter), self.registeredUsername, opponent)
						game.start()
						response = "NEGR#Success#Your opponent " + opponent + " is ready, press start to play"
					threadLock.release()
				elif requestParsed[0] == "WATG":
					threadLock.acquire()
					if len(activeGames) == 0:
						readyToWatchQueue.put(self.registeredUsername)
						response = "WAGR#Wait#There is no active game at the moment; you are added to waiting list"
					else:
						game = activeGames[0]
						game.addWatcher(self.registeredUsername)
						response = "WAGR#Success# Stay tuned for seeing this great game"
					threadLock.release()

		return response

# ------------------------GameThread------------------------
class gameThread(threading.Thread):
	
	def __init__(self, threadID, name, username1, username2):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.username1 = username1
		self.username2 = username2
		# Possible States
		self.Playing = "Playing" # String Constant
		self.PlayingInTurn = "PlayingInTurn" # String Constant
		# Initial States
		self.player1State = self.Playing
		self.player2State = self.Playing
		# Keep watchers connection
		self.watchers = []
		# Keep last move in mind for Wrong Play Alert
		self.lastMove = ""
	
	def run(self):
		print("GameThread is running for " + self.username1 + "-" + self.username2)
		# User 1 is informed that he is playing with user 2, inform user 2 here
	
	def addWatcher(self, usernameOfWatcher):
		print("AddWatcher function in gameThread is running")	

# ------------------------Global------------------------
# Queues
readyToPlayQueue = Queue.Queue(10)
readyToWatchQueue = Queue.Queue(1000)

# ActiveUsers {username, connection}
activeUsers = dict()
# ActiveGames {objectItself}
activeGames = []

threadCounter = 0

notValidRequest = "WRRE#Fail#Your request is not valid"
threadLock = threading.Lock()

debug = True # Can be manually changed

server = Server()
server.start()