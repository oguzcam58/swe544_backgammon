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
		print('Server socket is created and it is the listening mode on ' + self.host + ':' + str(self.port))

		heartBeatThread = HeartBeatThread(threadCounter, 'Thread-' + str(threadCounter))
		heartBeatThread.start()

		while True:
			connection, address = self.serverSocket.accept() # Establish connection with client.
			print('Got connection from ', address)

			threadLock.acquire()
			threadCounter += 1
			cThread = ClientThread(threadCounter, 'Thread-' + str(threadCounter), heartBeatThread, connection, None)
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
		if debug:
			print('Starting HeartBeatThread ' + str(self.threadID) + ' ' + self.name) # Debug message
		while True:
			if debug:
				print 'PING-PONG is starting' # Debug message
			# Delete users info if no pong received in last 15 seconds
			for username in self.pingSend:
				self.deleteFromActiveUsers(username, True)
				self.pingSend.remove(username)

			users = copy.copy(activeUsers) # Shallow copy
			for username, connection in users.iteritems():
				try:
					connection.send('PING')
					if username not in self.pingSend:
						self.pingSend.append(username)
				except:
					if debug:
						print('An exception occurred in HeartBeatThread-1') # Debug message
					self.deleteFromActiveUsers(username, True)
			self.checkWaitingClients()
			time.sleep(15)

	def deleteFromActiveUsers(self, username, closeConn):
		threadLock.acquire()
		if activeUsers.get(username, None):
			conn = activeUsers.get(username)
			if closeConn:
				conn.close()
			del activeUsers[username]
		try:
			if readyToPlayQueue.index(username) > -1:
				readyToPlayQueue.remove(username)
		except ValueError:
			if debug:
				print('An exception occurred in deleteFromActiveUsers-1') # Debug message
			pass
		try:
			if readyToWatchQueue.index(username) > -1:
				readyToWatchQueue.remove(username)
		except ValueError:
			if debug:
				print('An exception occurred in deleteFromActiveUsers-2') # Debug message
			pass
		threadLock.release()

	def pongReceived(self, username):
		try:
			if debug:
				print('Pong received username = ' + username) # Debug message
			self.pingSend.remove(username)
		except ValueError:
			print('An exception occurred in pongReceived-1 for user ' + username) # Debug message
			pass

	def checkWaitingClients(self):
		playQueue = copy.copy(readyToPlayQueue)
		while len(playQueue) > 0:
			user = getConnFromUsername(playQueue[0])
			request = user.recv(1024).strip()
			if request == 'PONG':
				if debug:
					print('PONG received by HeartBeatThread.checkWaitingClients from playQueue') # Debug message
				self.pongReceived(playQueue[0])
				if debug:
					print('PONG request is taken') # Debug message
			del playQueue[0]

		waitQueue = copy.copy(readyToWatchQueue)
		while len(waitQueue) > 0:
			user = getConnFromUsername(waitQueue[0])
			request = user.recv(1024).strip()
			if request == 'PONG':
				if debug:
					print('PONG received by HeartBeatThread.checkWaitingClients from waitQueue') # Debug message
				self.pongReceived(waitQueue[0])
				if debug:
					print('PONG request is taken') # Debug message
			del waitQueue[0]

# ------------------------ClientThread------------------------
class ClientThread(threading.Thread):

	def __init__(self, threadID, name, heartBeatThread, connection, username):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.heartBeatThread = heartBeatThread
		self.connection = connection
		self.registeredUsername = username if username else ''
		# Possible States
		self.Connectionless = 'Connectionless' # String Constant
		self.Connected = 'Connected' # String Constant
		# Initial State
		self.state = self.Connected if username else self.Connectionless

	def run(self):
		if debug:
			print('Starting ClientThread ' + str(self.threadID) + ' ' + self.name) # Debug message
		# Wait for client's requests, read and answer them
		while True:
			try:
				request = self.connection.recv(1024).strip()
				response, exit = self.parser(request)
				if response:
					self.connection.send(response)
					if 'QUIR' in response:
						self.heartBeatThread.deleteFromActiveUsers(self.registeredUsername, False)
			except:
				if debug:
					print('An exception occurred in ClientThread.run-1') # Debug message
				break
			if exit:
				break

		if debug:
			print('Exiting ClientThread ' + self.name) # Debug message

	def parser(self, request):
		# Make using global variable possible
		global threadCounter

		if debug:
			print('Incoming request : ' + request) # Debug message
		response = notValidRequest
		exit = False
		if request:
			requestParsed = request.split('#')

			# Connectionless state, no record on active users
			if self.state == self.Connectionless:
				if debug:
					print('Checking on Connectionless state') # Debug message

				if requestParsed[0] == 'CONN':
					response = 'CONR'
					username = requestParsed[1] if len(requestParsed) > 1 else None
					if username:
						if len(username) > 20:
							response += '#Fail#Username can be 20 characters maximum'
						else:
							threadLock.acquire()
							if not activeUsers.get(username, None):
								activeUsers[username] = self.connection
								response += '#Success#Welcome to SWE544 backgammon'
								self.registeredUsername = username
								self.state = self.Connected
							else:
								response += '#Busy#There is an active user with ' + username + ' username, please choose another username'
							threadLock.release()
					else:
						response = notValidRequest
				else:
					response = notValidRequest

			# Connected state
			elif self.state == self.Connected:
				if debug:
					print('Checking on Connected state') # Debug message

				if requestParsed[0] == 'PONG':
					if debug:
						print('PONG received by ClientThread.parser') # Debug message
					self.heartBeatThread.pongReceived(self.registeredUsername)
					return None, False
				elif requestParsed[0] == 'NEWG':
					if debug:
						print('NEWG request is taken') # Debug message
					threadLock.acquire()
					if len(readyToPlayQueue) == 0:
						readyToPlayQueue.append(self.registeredUsername)
						response = 'NEGR#Wait#There is no one wants to play at the moment; you are added to waiting list'
					else:
						opponent = readyToPlayQueue[0]
						del readyToPlayQueue[0]
						threadCounter += 1
						game = GameThread(threadCounter, 'Thread-' + str(threadCounter), self.heartBeatThread, self.registeredUsername, opponent)
						game.start()
						response = 'NEGR#Success#Your opponent ' + opponent + ' is ready, game is beginning'
					threadLock.release()
					exit = True
				elif requestParsed[0] == 'WATG':
					if debug:
						print('WATG request is taken') # Debug message
					threadLock.acquire()
					if len(activeGames) == 0:
						readyToWatchQueue.append(self.registeredUsername)
						response = 'WAGR#Wait#There is no active game at the moment; you are added to waiting list'
					else:
						game = activeGames[0]
						game.addWatcher(self.registeredUsername, True)
						response = 'WAGR#Success# Stay tuned for seeing this great game'
					threadLock.release()
					exit = True
				elif requestParsed[0] == 'QUIT':
					response = 'QUIR#Success#Goodbye'
					self.state = self.Connectionless

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
		self.Playing = 'Playing' # String Constant
		self.PlayingInTurn = 'PlayingInTurn' # String Constant
		self.GoingOn = 'Going on'
		self.Over = 'Over'
		# Initial States
		self.player1State = self.Playing
		self.player2State = self.Playing
		self.gameState = self.GoingOn
		self.winner = ''
		# Keep watchers connection
		self.watchers = []
		# Keep last move in mind for Wrong Play Alert
		self.lastMove = ''

		# GameBoard 0-23 for checkers on board, 25 (index 24) for collection area and 26 (index 25) for hit checkers
		# In every row, first column is used for white checkers (O), second for black checkers (X)
		self.gameBoard = [[0 for x in range(2)] for x in range(26)] # White, black

		# White checkers default position
		self.gameBoard[0][0] = 2
		self.gameBoard[11][0] = 5
		self.gameBoard[16][0] = 3
		self.gameBoard[18][0] = 5

		# Black checkers default position
		self.gameBoard[23][1] = 2
		self.gameBoard[12][1] = 5
		self.gameBoard[7][1] = 3
		self.gameBoard[5][1] = 5

		# Queues to receive messages
		self.player1Queue = Queue.Queue()
		self.player2Queue = Queue.Queue()
		self.notifyQueue = Queue.Queue()

	def run(self):
		global threadCounter

		threadLock.acquire()
		activeGames.append(self)
		threadCounter += 1
		gameReaderThread = GameReaderThread(threadCounter, 'Thread-' + str(threadCounter), self)
		gameReaderThread.start()
		threadCounter += 1
		watcherThread = WatcherThread(threadCounter, 'Thread-' + str(threadCounter), self)
		watcherThread.start()
		threadCounter += 1
		notifyWatchersThread = NotifyWatchersThread(threadCounter, 'Thread-' + str(threadCounter), self)
		notifyWatchersThread.start()
		threadLock.release()

		if debug:
			print('Starting GameThread for ' + self.username1 + '-' + self.username2) # Debug message

		# User 1 is informed that he is playing with user 2, inform user 2 here
		self.player2.send('NEGR#Success#Your opponent ' + self.username1 + ' is ready, game is beginning')

		# Add waiting watchers to the game
		self.getWatchersFromQueue()

		whoWillStart = randint(0,1)
		self.player1.send('INFO#Wait#Your checkers are signed with O')
		self.player2.send('INFO#Wait#Your checkers are signed with X')
		time.sleep(1)

		if whoWillStart == 0:
			whoWillPlay = 0
		else:
			whoWillPlay = 1

		while self.gameState != self.Over:
			whoWillPlay = 1 if whoWillPlay == 0 else 0
			if whoWillPlay == 0:
				self.throwDice(self.player1, self.player2)
			else:
				self.throwDice(self.player2, self.player1)

		finishMessage = 'OVER#' + self.winner + 'wins the game'
		if activeUsers.get(self.username1, None):
			try:
				self.player1.send(finishMessage)
			except:
				pass
		if activeUsers.get(self.username2, None):
			try:
				self.player2.send(finishMessage)
			except:
				pass

		threadLock.acquire()
		threadCounter += 1
		cThread = ClientThread(threadCounter, 'Thread-' + str(threadCounter), self.heartBeatThread, self.player1, self.username1)
		cThread.start()
		cThread = ClientThread(threadCounter, 'Thread-' + str(threadCounter), self.heartBeatThread, self.player2, self.username2)
		cThread.start()
		threadLock.release()

		activeGames.remove(self)

		if debug:
			print('Exiting GameThread ' + self.name) # Debug message

	def throwDice(self, playerInTurn, playerOther):
		# Check if users still active
		if not activeUsers.get(self.username1, None) or self.gameBoard[24][1] == 15:
			self.gameState = self.Over
			self.winner = self.username2
			return
		if not activeUsers.get(self.username2, None) or self.gameBoard[24][0] == 15:
			self.gameState = self.Over
			self.winner = self.username1
			return

		dice1 = str(randint(1,6))
		dice2 = str(randint(1,6))

		playerInTurn.send( 'THRD#Success#' + dice1 + '-' + dice2 )
		playerOther.send( 'THRD#Wait#' + dice1 + '-' + dice2 )
		self.notifyQueue.put( 'THRD#Wait#' + dice1 + '-' + dice2 )

		# Wait for client's requests, read and answer them
		while self.gameState != self.Over:
			exit = False
			try:
				request = None
				if self.player1 == playerInTurn and not self.player1Queue.empty():
					request = self.player1Queue.get()
					if debug:
						print(request) # Debug messsage
				if self.player2 == playerInTurn and not self.player2Queue.empty():
					request = self.player2Queue.get()
					if debug:
						print(request) # Debug messsage

				if request:
					response, exit = self.parser(request, 0 if playerInTurn == self.player1 else 1)
					if response:
						playerInTurn.send(response)
						if exit:
							playerOther.send(response)
							self.notifyQueue.put(response)
							if response[0:4] == 'SNMR' and request[0:4] == 'SNDM':
								parts = response.split('#')
								self.lastMove = parts[len(parts) - 1]
								self.lastDice = dice1 + '-' + dice2
							else: # After Wrong Play Alert set last move empty
								self.lastMove = ''
								self.lastDice = ''

			except:
				if debug:
					print('An exception occurred in throwDice-1') # Debug message
				break
			if exit:
				break

	def parser(self, request, player):
		if debug:
			print('Incoming request : ' + request) # Debug message
		response = notValidRequest
		exit = False
		if request:
			requestParsed = request.split('#')
			if debug:
				print('Checking on PlayingInTurn state') # Debug message
			if requestParsed[0] == 'SNDM':
				moves = requestParsed[1].split(',')
				response = 'SNMR#' + str(player) + '#'
				exit = True
				if len(moves) < 5:
					for move in moves:
						if move == None or move == '':
							continue
						move.strip()
						places = move.split('-')
						if places == None or places == '':
							continue
						try:
							checkerOldPlace = int(places[0].strip()) - 1
							checkerNewPlace = int(places[1].strip()) - 1
							if checkerOldPlace < 26 and checkerNewPlace < 26 and self.gameBoard[checkerOldPlace][player] > 0:
								self.gameBoard[checkerOldPlace][player] -= 1
								self.gameBoard[checkerNewPlace][player] += 1
								response += places[0] + '-' + places[1] + ','
							else:
								response = 'INFO#Fail#You should check your moves'
								exit = False
								return response, exit
						except:
							if debug:
								print('An exception occurred in GameThread.parser-1') # Debug message
				else:
					response = 'INFO#Fail#You should check your moves'
					exit = False
			elif requestParsed[0] == 'WRNG':
				if self.lastMove != None and self.lastMove != '':
					move = self.revertLastMove()
					response = 'SNMR#' + str(0 if player == 1 else 1) + '#' + move
					exit = True
		return response, exit

	def pongReceived(self, player):
		if player == self.player1:
			if debug:
				print('PONG received by GameThread.pongReceived for username1') # Debug message
			self.heartBeatThread.pongReceived(self.username1)
		if player == self.player2:
			if debug:
				print('PONG received by GameThread.pongReceived for username2') # Debug message
			self.heartBeatThread.pongReceived(self.username2)

	def addWatcher(self, usernameOfWatcher, gameBoardSend):
		if debug:
			print('AddWatcher function in gameThread is running') # Debug message
		connection = getConnFromUsername(usernameOfWatcher)
		if connection:
			self.watchers.append(connection)
			if gameBoardSend:
				gameBoardString = ''
				for i in range(0, len(self.gameBoard) -1):
					if self.gameBoard[i][0] > 0:
						gameBoardString += str(i) + '-' + str(0) + '-' + str(self.gameBoard[i][0]) + ','
					if self.gameBoard[i][1] > 0:
						gameBoardString += str(i) + '-' + str(1) + '-' + str(self.gameBoard[i][1]) + ','
				connection.send('GMBR#' + gameBoardString) # Send complete gameboard
				time.sleep(1)
			connection.send('WAGR#Success#Stay tuned for seeing this great game of players ' + self.username1 + ' and ' + self.username2)

	def deleteWatcher(self, connection):
		self.watchers.remove(connection)

	def getWatchersFromQueue(self):
		threadLock.acquire()
		while len(readyToWatchQueue) > 0:
			self.addWatcher(readyToWatchQueue[0], False)
			del readyToWatchQueue[0]
		threadLock.release()

	def revertLastMove(self):
		revertedMove = ''
		moves = self.lastMove.split(',')
		for move in moves:
			if move == None or move == '':
				continue
			places = move.split('-')
			if places == None or places == '':
				continue
			revertedMove += places[1] + '-' + places[0] + ','
		return revertedMove

# ------------------------GameReaderThread------------------------
class GameReaderThread(threading.Thread):

	def __init__(self, threadID, name, gameThread):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.gameThread = gameThread
		self.player1 = gameThread.player1
		self.player2 = gameThread.player2
	def run(self):
		if debug:
			print('Starting GameReaderThread ' + self.name) # Debug message
		while self.gameThread.gameState != self.gameThread.Over:
			try:
				request = self.player1.recv(1024).strip()
				if request:
					if debug:
						print(request) # Debug messsage
					if 'PONG' in request:
						if debug:
							print('PONG received by GameReaderThread.run for player1') # Debug message
						self.gameThread.pongReceived(self.player1)
						requestPongIncluded = request.split('PONG')
						if requestPongIncluded != None and requestPongIncluded != '':
							if len(requestPongIncluded) > 1:
								requestWithoutPong = requestPongIncluded[0] + requestPongIncluded[1]
								if requestWithoutPong != None and requestWithoutPong != '':
									self.gameThread.player1Queue.put(requestWithoutPong)
					else:
						self.gameThread.player1Queue.put(request)
			except:
				if debug:
					print('An exception occurred in GameReaderThread-1') # Debug message
				self.gameThread.heartBeatThread.deleteFromActiveUsers(getUsernameFromConn(self.gameThread.username1), True)
				self.gameThread.gameState = self.gameThread.Over

			try:
				request2 = self.player2.recv(1024).strip()
				if request2:
					if debug:
						print(request2) # Debug Message
					if 'PONG' in request2:
						if debug:
							print('PONG received by GameReaderThread.run for player2') # Debug message
						self.gameThread.pongReceived(self.player2)
						request2PongIncluded = request2.split('PONG')
						if request2PongIncluded != None and request2PongIncluded != '':
							if len(request2PongIncluded) > 1:
								requestWithoutPong = request2PongIncluded[0] + request2PongIncluded[1]
								if requestWithoutPong != None and requestWithoutPong != '':
									self.gameThread.player2Queue.put(requestWithoutPong)
					else:
						self.gameThread.player2Queue.put(request2)
			except:
				if debug:
					print('An exception occurred in GameReaderThread-2') # Debug message
				self.gameThread.heartBeatThread.deleteFromActiveUsers(getUsernameFromConn(self.gameThread.username2), True)
				self.gameThread.gameState = self.gameThread.Over

# ------------------------WatcherThread------------------------
class WatcherThread(threading.Thread):

	def __init__(self, threadID, name, gameThread):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.gameThread = gameThread
		self.watchers = []
	def run(self):
		global threadCounter
		if debug:
			print('Starting WatcherThread ' + self.name) # Debug message
		while self.gameThread.gameState != self.gameThread.Over:
			self.watchers = copy.copy(self.gameThread.watchers)
			for watcher in self.watchers:
				watcherUsername = getUsernameFromConn(watcher)
				if not watcherUsername:
					self.gameThread.deleteWatcher(watcher)
				else:
					request = watcher.recv(1024).strip()
					if request:
						if debug:
							print('Check watcher messages for watcher ' + watcherUsername)
						if 'PONG' in request:
							if debug:
								print('PONG received by WatcherThread.run from ' + watcherUsername)
							self.gameThread.heartBeatThread.pongReceived(watcherUsername)
						if 'LEAW' in request:
							self.gameThread.deleteWatcher(watcher)
							self.watcher.send('LEWR#Success#You left watching the game, you may continue with others')
							threadLock.acquire()
							threadCounter += 1
							cThread = ClientThread(threadCounter, 'Thread-' + str(threadCounter), self.gameThread.heartBeatThread, watcher, watcherUsername)
							threadLock.release()

# ------------------------NotifyWatcherThread------------------------
class NotifyWatchersThread(threading.Thread):

	def __init__(self, threadID, name, gameThread):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.gameThread = gameThread
	def run(self):
		if debug:
			print('Starting NotifyWatchersThread ' + self.name) # Debug message
		while self.gameThread.gameState != self.gameThread.Over:
			if not self.gameThread.notifyQueue.empty():
				message = self.gameThread.notifyQueue.get()
				for watcher in self.gameThread.watchers:
					watcherUsername = getUsernameFromConn(watcher)
					if not watcherUsername:
						self.gameThread.deleteWatcher(watcher)
					else:
						if debug:
							print('Notify watcher ' + watcherUsername + str(len(self.gameThread.watchers)))
						try:
							watcher.send(message)
						except:
							pass

		for watcher in self.gameThread.watchers:
			watcherUsername = getUsernameFromConn(watcher)
			if not watcherUsername:
				print('Delete watcher from game with username ' + watcherUsername)
				self.gameThread.deleteWatcher(watcher)
			try:
				watcher.send('OVER#' + self.gameThread.winner + ' wins the game')
				threadLock.acquire()
				threadCounter += 1
				cThread = ClientThread(threadCounter, 'Thread-' + str(threadCounter), self.gameThread.heartBeatThread, watcher, watcherUsername)
				threadLock.release()
			except:
				pass

# ------------------------Global Variables------------------------
# Lists {username}
readyToPlayQueue = []
readyToWatchQueue = []

# ActiveUsers {username, connection}
activeUsers = dict()
# ActiveGames {objectItself}
activeGames = []

threadCounter = 1

notValidRequest = 'WRRE#Fail#Your request is not valid'
threadLock = threading.Lock()

debug = True # Can be manually changed

# ------------------------Global Methods------------------------
def getConnFromUsername(username):
	connection = activeUsers.get(username, None)
	if not connection and debug:
		print(username + ' has no connection') # Debug message
	return connection

def getUsernameFromConn(connection):
	for username, conn in activeUsers.items():
		if conn == connection:
			return username
	return None

# ------------------------Main Program Functionality------------------------
server = Server()
server.start()