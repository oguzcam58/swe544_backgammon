#!/usr/bin/env python
import Queue # Import queue module
import socket # Import socket module
import threading # Import threading module
import copy # Import copy module
import time # Import time module
from random import randint # Import randint method

# ------------------------Server------------------------
class Server:
	serverSocket = socket.socket() # Create a socket object
	host = socket.gethostname() # Get local machine name
	port = 12345 # Reserve a port for your service.

	def start(self):
		# Make using global variable possible
		global threadCounter

		self.serverSocket.bind((self.host, self.port)) # Bind to the port
		self.serverSocket.listen(1000) # Now wait for client connection.
		print('Server socket is created and it is the listening mode on ' + self.host + ":" + str(self.port))

		heartBeatThread = HeartBeatThread(threadCounter, "Thread-" + str(threadCounter))
		heartBeatThread.start()

		while True:
			connection, address = self.serverSocket.accept() # Establish connection with client.
			print('Got connection from ', address)

			threadLock.acquire()
			threadCounter += 1
			cThread = ClientThread(threadCounter, "Thread-" + str(threadCounter), heartBeatThread, connection, address)
			threadLock.release()

			cThread.start()

# ------------------------HeartBeatThread------------------------
class HeartBeatThread(threading.Thread):

	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.pingSend = []

	def run(self):
		print("Starting thread " + str(self.threadID) + " " + self.name)
		while True:
			if debug:
					print "PING-PONG is starting" # Debug message
			# Delete users info if no pong received in last 15 seconds
			for username in self.pingSend:
				self.deleteFromActiveUsers(username)
				self.pingSend.remove(username)

			users = copy.copy(activeUsers) # Shallow copy
			for username, connection in users.iteritems():
				try:
					connection.send("PING")
					self.pingSend.append(username)
				except:
					if debug:
						print("An exception occurred") # Debug message
						raise
					self.deleteFromActiveUsers(username)
			self.checkWaitingClients()
			time.sleep(15)

	def deleteFromActiveUsers(self, username):
		if debug:
			print username + " is being deleted from active users list because of no response to heartbeat messages" # Debug message

		threadLock.acquire()
		if activeUsers.get(username, None):
			del activeUsers[username]
		try:
			if readyToPlayQueue.index(username) > -1:
				readyToPlayQueue.remove(username)
		except ValueError:
			pass
		try:
			if readyToWatchQueue.index(username) > -1:
				readyToWatchQueue.remove(username)
		except ValueError:
			pass
		threadLock.release()

	def pongReceived(self, username):
		self.pingSend.remove(username)

	def checkWaitingClients(self):
		threadLock.acquire()
		playQueue = copy.copy(readyToPlayQueue)
		while len(playQueue) > 0:
			user = getConnFromUsername(playQueue[0])
			request = user.recv(1024).strip()
			if request == "PONG":
				self.pongReceived(playQueue[0])
				if debug:
					print("PONG request is taken") # Debug message
			del playQueue[0]

		waitQueue = copy.copy(readyToWatchQueue)
		while len(waitQueue) > 0:
			user = getConnFromUsername(waitQueue[0])
			request = user.recv(1024).strip()
			if request == "PONG":
				self.pongReceived(waitQueue[0])
			del waitQueue[0]
		threadLock.release()

# ------------------------ClientThread------------------------
class ClientThread(threading.Thread):

	def __init__(self, threadID, name, heartBeatThread, connection, address):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.heartBeatThread = heartBeatThread
		self.connection = connection
		self.address = address
		self.registeredUsername = ""
		# Possible States
		self.Connectionless = "Connectionless" # String Constant
		self.Connected = "Connected" # String Constant
		# Initial State
		self.state = self.Connectionless

	def run(self):

		print("Starting ClientThread " + str(self.threadID) + " " + self.name + " " + str(self.address))
		# Wait for client's requests, read and answer them
		while True:
			try:
				request = self.connection.recv(1024).strip()
				response, exit = self.parser(request)
				if response:
					self.connection.send(response)
			except:
				if debug:
					print("An exception occurred") # Debug message
					raise
				break
			if exit:
				break

		if debug:
			print("Exiting ClientThread " + self.name) # Debug message

	def parser(self, request):
		# Make using global variable possible
		global threadCounter

		if debug:
			print("Incoming request : " + request) # Debug message
		response = notValidRequest
		exit = False
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

				if requestParsed[0] == "PONG":
					if debug:
						print("PONG request is taken") # Debug message
					self.heartBeatThread.pongReceived(self.registeredUsername)
					return None, False
				elif requestParsed[0] == "NEWG":
					if debug:
						print("NEWG request is taken") # Debug message
					threadLock.acquire()
					if len(readyToPlayQueue) == 0:
						readyToPlayQueue.append(self.registeredUsername)
						response = "NEGR#Wait#There is no one wants to play at the moment; you are added to waiting list"
					else:
						opponent = readyToPlayQueue[0]
						del readyToPlayQueue[0]
						threadCounter += 1
						game = GameThread(threadCounter, "Thread-" + str(threadCounter), self.heartBeatThread, self.registeredUsername, opponent)
						game.start()
						response = "NEGR#Success#Your opponent " + opponent + " is ready, game is beginning"
					threadLock.release()
					exit = True
				elif requestParsed[0] == "WATG":
					if debug:
						print("WATG request is taken") # Debug message
					threadLock.acquire()
					if len(activeGames) == 0:
						readyToWatchQueue.append(self.registeredUsername)
						response = "WAGR#Wait#There is no active game at the moment; you are added to waiting list"
					else:
						game = activeGames[0]
						game.addWatcher(self.registeredUsername)
						response = "WAGR#Success# Stay tuned for seeing this great game"
						exit = True
					threadLock.release()

		return response, exit


# ------------------------GameThread------------------------
class GameThread(threading.Thread):

	def __init__(self, threadID, name, heartBeatThread, username1, username2):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.heartBeatThread = heartBeatThread
		self.username1 = username1
		self.username2 = username2
		# Get connections for players
		self.player1 = getConnFromUsername(username1)
		self.player2 = getConnFromUsername(username2)
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

		# GameState 0-23 for checkers on board, 24 for collection area and 25 for hit checkers
		# In every row, first column is used for white checkers (O), second for black checkers (X)
		self.gameState = [[0 for x in range(2)] for x in range(26)] # White, black

		# White checkers default position
		self.gameState[0][0] = 2
		self.gameState[11][0] = 5
		self.gameState[16][0] = 3
		self.gameState[18][0] = 5

		# Black checkers default position
		self.gameState[23][1] = 2
		self.gameState[12][1] = 5
		self.gameState[7][1] = 3
		self.gameState[5][1] = 5

	def run(self):
		threadLock.acquire()
		activeGames.append(self)
		threadLock.release()
		if debug:
			print("Starting GameThread for " + self.username1 + "-" + self.username2) # Debug message

		# User 1 is informed that he is playing with user 2, inform user 2 here
		self.player2.send("NEGR#Success#Your opponent " + self.username1 + " is ready, game is beginning")

		# Add waiting watchers to the game
		self.getWatchersFromQueue()

		whoWillStart = randint(0,1)
		self.player1.send("INFO#Wait#Your checkers are signed with O")
		self.player2.send("INFO#Wait#Your checkers are signed with X")
		time.sleep(1)

		if whoWillStart == 0:
			self.throwDice(self.player1, self.player2)
		else:
			self.throwDice(self.player2, self.player1)

		if debug:
			print("Exiting GameThread " + self.name) # Debug message

	def parser(self, request):
		if debug:
			print("Incoming request : " + request) # Debug message
		response = notValidRequest
		exit = False
		if request:
			requestParsed = request.split("#")
			if debug:
				print("Checking on PlayingInTurn state") # Debug message
			if requestParsed[0] == "SNDM":
				if debug:
					print("SNDM request is taken") # Debug message
		return response, exit

	def throwDice(self, playerInTurn, playerOther):
		dice1 = str(randint(1,6))
		dice2 = str(randint(1,6))

		playerInTurn.send( "THRD#Success#" + dice1 + "-" + dice2 )
		playerOther.send( "THRD#Wait#" + dice1 + "-" + dice2 )
		#notifyWatchersDice(username1, dice1, dice2)

		# Wait for client's requests, read and answer them
		while True:
			exit = False
			try:
				request = playerInTurn.recv(1024).strip()
				requestOther = playerOther.recv(1024).strip()

				if requestOther: # It just can send PONG messages
					if requestOther == "PONG":
						self.pongReceived(playerOther)

				if request:
					if request == "PONG":
						self.pongReceived(playerInTurn)
					else:
						response, exit = self.parser(request)
						if response:
							playerInTurn.send(response)
							playerOther.send(response)
			except:
				if debug:
					print("An exception occurred") # Debug message
					raise
				break
			if exit:
				break

	def pongReceived(self, player):
		if player == self.player1:
			self.heartBeatThread.pongReceived(self.username1)
		if player == self.player2:
			self.heartBeatThread.pongReceived(self.username2)

	def addWatcher(self, usernameOfWatcher):
		if debug:
			print("AddWatcher function in gameThread is running") # Debug message
		connection = getConnFromUsername(usernameOfWatcher)
		if connection:
			self.watchers.append(connection)
			connection.send("WAGR#Success#Stay tuned for seeing this great game of players " + self.username1 + " and " + self.username2)

	def getWatchersFromQueue(self):
		threadLock.acquire()
		while len(readyToWatchQueue) > 0:
			self.addWatcher(readyToWatchQueue[0])
			del readyToWatchQueue[0]
		threadLock.release()


# ------------------------Global Variables------------------------
# Queues {username}
readyToPlayQueue = []
readyToWatchQueue = []

# ActiveUsers {username, connection}
activeUsers = dict()
# ActiveGames {objectItself}
activeGames = []

threadCounter = 1

notValidRequest = "WRRE#Fail#Your request is not valid"
threadLock = threading.Lock()

debug = False # Can be manually changed

# ------------------------Global Methods------------------------
def getConnFromUsername(username):
	connection = activeUsers.get(username, None)
	if not connection and debug:
		print(username + " has no connection") # Debug message
	return connection

# ------------------------Main Program Functionality------------------------
server = Server()
server.start()