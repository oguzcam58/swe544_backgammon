#!/usr/bin/env python
import socket # Import socket module
import threading # Import threading module
import Queue # Import Queue Module

# ------------------------Client------------------------
class Client:

	def __init__(self):
		self.clientSocket = socket.socket() # Create a socket object
		self.host = socket.gethostname() # Get local machine name
		self.port = 12345 # Reserve a port for your service.
		# Possible States
		self.Connectionless = 'Connectionless'
		self.Connected = 'Connected'
		self.Playing = 'Playing'
		self.PlayingInTurn = 'PlayingInTurn'
		self.Watching = 'Watching'
		# Default State
		self.state = self.Connectionless
		# GameState 0-23 for checkers on board, 24 for collection area and 25 for hit checkers.
		# In every row, first column is used for White checkers (O), Second for black checkers (X)
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
		self.response = None
		self.readerQueue = Queue.Queue()
	def connect(self):
		self.clientSocket.connect((self.host, self.port))
		readerThread = ReaderThread(1, 'Thread-1', self.clientSocket, self)
		readerThread.start()

		while True:
			protocol = ''
			if self.state == self.Connectionless:
				print 'Please choose a username: '
				protocol = 'CONN#'
			elif self.state == self.Connected:
				print 'To play game, please write NEWG. To watch a game, please write WATG'
			elif self.state == self.PlayingInTurn:
				print 'Make your move by entering current place of the checker and last place of the checker after a dash, separate your moves by comma for example if you throw 6-2: 3-5, 10-16 '
				print 'To collect checkers use place 25 '
				print 'To play hit checkers use place 26 '
				protocol = 'SNDM#'

			inputByUser = raw_input('')
			if inputByUser == 'WRNG':
				protocol = ''

			request = protocol + inputByUser
			self.clientSocket.send(request)
			while True:
				response = self.readerQueue.get()
				if response:
					isWait = self.clientParser(response)
					if not isWait and self.readerQueue.empty():
						break

		print 'Exiting Client'
		# Quit
		self.clientSocket.close()

	def setResponse(self, response):
		self.readerQueue.put(response)

	def clientParser(self, response):
		Success = 'Success' # String Constant
		Fail = 'Fail' # String Constant
		Busy = 'Busy' # String Constant
		Wait = 'Wait' # String Constant

		isWait = False
		if response:
			printMessage = True
			responseParsed = response.split('#')
			if len(responseParsed) > 1:
				if responseParsed[0] == 'CONR' and responseParsed[1] == Success:
					self.state = self.Connected
				elif (responseParsed[0] == 'NEGR' or responseParsed[0] == 'WAGR'):
					if responseParsed[1] == Success:
						if responseParsed[0] == 'NEGR':
							self.state = self.Playing
						else:
							self.state = self.Watching
						printMessage = False
						print ''
						print(responseParsed[len(responseParsed) - 1])
						print ''
						self.drawGameBoard(self.gameBoard)
					isWait = True
				elif responseParsed[0] == 'INFO':
					if responseParsed[1] == Wait:
						isWait = True
				elif responseParsed[0] == 'THRD':
					self.state = self.Playing
					if responseParsed[1] == Success:
						self.state = self.PlayingInTurn
						print 'Dice: ' + responseParsed[2]
						print 'It is your turn to play'
						printMessage = False
						isWait = False
					else:
						print 'Dice: ' + responseParsed[2]
						printMessage = False
						isWait = True
						print ''
				elif responseParsed[0] == 'SNMR':
					isWait = True
					if debug:
						print response # Debug message
					moves = responseParsed[2].split(',')
					for move in moves:
						if move == None or move == '':
							continue
						move.strip()
						places = move.split('-')
						if places == None or places == '':
							continue
						checkerOldPlace = int(places[0].strip()) - 1
						checkerNewPlace = int(places[1].strip()) - 1
						self.gameBoard[checkerOldPlace][int(responseParsed[1])] -= 1
						self.gameBoard[checkerNewPlace][int(responseParsed[1])] += 1
						self.drawGameBoard(self.gameBoard)
						print ''
				elif responseParsed[0] == 'GMBR':
					self.makeZeroGameBoard()
					isWait = True
					if responseParsed[1] != None and responseParsed[1] != '':
						self.state = self.Watching
						checkers = responseParsed[1].split(',')
						for checker in checkers:
							if checker == None or checker == '':
								continue
							places = checker.split('-')
							if places == None or places == '' or len(places) < 3:
								continue
							self.gameBoard[int(places[0])][int(places[1])] = int(places[2])

						self.drawGameBoard(self.gameBoard)
						printMessage = False

				elif responseParsed[0] == 'LEWR':
					self.state = self.Connected
				elif responseParsed[0] == 'OVER':
					self.state = self.Connected
				elif responseParsed[0] == 'QUIR':
					self.state = self.Connectionless

			if printMessage:
				print(responseParsed[len(responseParsed) - 1])
		return isWait

	def makeZeroGameBoard(self):
		# White checkers default position
		self.gameBoard[0][0] = 0
		self.gameBoard[11][0] = 0
		self.gameBoard[16][0] = 0
		self.gameBoard[18][0] = 0
		# Black checkers default position
		self.gameBoard[23][1] = 0
		self.gameBoard[12][1] = 0
		self.gameBoard[7][1] = 0
		self.gameBoard[5][1] = 0

	def drawGameBoard(self, gameBoard):
		self.drawTitle(13, 25)
		self.drawFirstPart(gameBoard)
		self.drawEmptyLine(17)
		self.drawSecondPart(gameBoard)
		self.drawTitle(12, 0)

	def drawFirstPart(self, gameBoard):
		counter = 0
		isCheckerAvailable = True
		while isCheckerAvailable:
			line = '|'
			counter += 1
			checkerCount = 0
			for i in range(12,24):
				if i == 18:
					line += '|' + str.ljust(' ', 5) + '|'

				if gameBoard[i][0] >= counter:
					line += ' O'
					checkerCount += 1
				elif gameBoard[i][1] >= counter:
					line += ' X'
					checkerCount += 1
				else:
					line += '  '

				if i != 17 and i != 23:
					line += ' '

			line += '|'
			print(line)

			if counter >= 5 and checkerCount == 0:
				isCheckerAvailable = False

	def drawSecondPart(self, gameBoard):
		maxChecker = self.maxCheckerInACol(gameBoard, 11, -1)
		for counter in range(maxChecker, 0, -1):
			line = '|'
			for i in range(11, -1, -1):
				if i == 5:
					line += '|' + str.ljust(' ', 5) + '|'

				if gameBoard[i][0] >= counter:
					line += ' O'
				elif gameBoard[i][1] >= counter:
					line += ' X'
				else:
					line += '  '

				if i != 6 and i != 0:
					line += ' '

			line += '|'
			print(line)


	def drawEmptyLine(self, spaceCount):
		print '|' + str.ljust(' ', spaceCount) + '|',
		print 'BAR',
		print '|' + str.ljust(' ', spaceCount) + '|'
		print '|' + str.ljust(' ', spaceCount) + '|',
		print '   ',
		print '|' + str.ljust(' ', spaceCount) + '|'

	def maxCheckerInACol(self, gameBoard, first, last):
		if first == last:
			return None

		max = 0
		if first > last:
			for i in range(first, last, -1):
				max = gameBoard[i][0] if gameBoard[i][0] > max else max
				max = gameBoard[i][1] if gameBoard[i][1] > max else max
		else:
			for i in range(last, first):
				max = gameBoard[i][0] if gameBoard[i][0] > max else max
				max = gameBoard[i][1] if gameBoard[i][1] > max else max
		return max

	def drawTitle(self, firstCol, lastCol):
		line = '-'
		counter = 0
		if firstCol < lastCol:
			for num in range(firstCol, lastCol):
				line += str(num) + '-'
				counter += 1
				if counter == 6:
					line += '------'
			print line
		else:
			for num in range(firstCol, lastCol, -1):
				if num < 10:
					line += '-'
				line += str(num) + '-'
				counter += 1
				if counter == 6:
					line += '------'
			print line

# ------------------------ReaderThread------------------------
class ReaderThread(threading.Thread):
	def __init__(self, threadId, name, connection, clientThread):
		threading.Thread.__init__(self)
		self.connection = connection
		self.clientThread = clientThread

	def run(self):
		while True:
			response = self.connection.recv(1024).strip()
			if response:
				if debug:
					print(response) # Debug messsage
				if 'PING' in response:
					self.connection.send('PONG')
					responsePingIncluded = response.split('PING')
					if responsePingIncluded != None and responsePingIncluded != '':
						if len(responsePingIncluded) > 1:
							requestWithoutPing = responsePingIncluded[0] + responsePingIncluded[1]
							if requestWithoutPing != None and requestWithoutPing != '':
								self.clientThread.setResponse(requestWithoutPing)
				else:
					self.clientThread.setResponse(response)

# ------------------------Global Variables------------------------
debug = False

# ------------------------Main Program Functionality------------------------
client = Client()
client.connect()
