#!/usr/bin/env python
import socket # Import socket module
import threading # Import threading module

# ------------------------Client------------------------
class Client:
	def __init__(self):
		self.clientSocket = socket.socket() # Create a socket object
		self.host = socket.gethostname() # Get local machine name
		self.port = 12345 # Reserve a port for your service.

		# GameState 0-23 for checkers on board, 24 for collection area and 25 for hit checkers.
		# In every row, first column is used for White checkers (O), Second for black checkers (X)
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

		self.response = None

	def connect(self):
		self.clientSocket.connect((self.host, self.port))
		readerThread = ReaderThread(1, "Thread-1", self.clientSocket, self)
		readerThread.start()

		while True:
			request = raw_input("Say something")
			self.clientSocket.send(request)
			while True:
				response = self.response

				if response:
					isWait = self.clientParser(response)
					self.setResponse(None)
					if not isWait:
						break
		# Quit
		self.clientSocket.close()

	def setResponse(self, response):
		self.response = response

	def clientParser(self, response):
		Success = "Success" # String Constant
		Fail = "Fail" # String Constant
		Busy = "Busy" # String Constant
		Wait = "Wait" # String Constant

		isWait = False
		if response != None:
			responseParsed = response.split("#")
			if len(responseParsed) > 1:
				if (responseParsed[0] == "NEGR" or responseParsed[0] == "WAGR"):
					if responseParsed[1] == Success:
						self.drawGameBoard(self.gameState)
					isWait = True

			if responseParsed:
				print(responseParsed[len(responseParsed) - 1])
		return isWait

	def drawGameBoard(self, gameState):
		self.drawTitle(13, 25)
		self.drawFirstPart(gameState)
		self.drawEmptyLine(17)
		self.drawSecondPart(gameState)
		self.drawTitle(12, 0)

	def drawFirstPart(self, gameState):
		counter = 0
		isCheckerAvailable = True
		while isCheckerAvailable:
			line = "|"
			counter += 1
			checkerCount = 0
			for i in range(12,24):
				if i == 18:
					line += '|' + str.ljust(' ', 5) + '|'

				if gameState[i][0] >= counter:
					line += " O"
					checkerCount += 1
				elif gameState[i][1] >= counter:
					line += " X"
					checkerCount += 1
				else:
					line += "  "

				if i != 17 and i != 23:
					line += " "

			line += "|"
			print(line)

			if counter >= 5 and checkerCount == 0:
				isCheckerAvailable = False

	def drawSecondPart(self, gameState):
		maxChecker = self.maxCheckerInACol(gameState, 11, -1)
		for counter in range(maxChecker, 0, -1):
			line = "|"
			for i in range(11, -1, -1):
				if i == 5:
					line += '|' + str.ljust(' ', 5) + '|'

				if gameState[i][0] >= counter:
					line += " O"
				elif gameState[i][1] >= counter:
					line += " X"
				else:
					line += "  "

				if i != 6 and i != 0:
					line += " "

			line += "|"
			print(line)


	def drawEmptyLine(self, spaceCount):
		print '|' + str.ljust(' ', spaceCount) + '|',
		print 'BAR',
		print '|' + str.ljust(' ', spaceCount) + '|'
		print '|' + str.ljust(' ', spaceCount) + '|',
		print '   ',
		print '|' + str.ljust(' ', spaceCount) + '|'

	def maxCheckerInACol(self, gameState, first, last):
		if first == last:
			return None

		max = 0
		if first > last:
			for i in range(first, last, -1):
				max = gameState[i][0] if gameState[i][0] > max else max
				max = gameState[i][1] if gameState[i][1] > max else max
		else:
			for i in range(last, first):
				max = gameState[i][0] if gameState[i][0] > max else max
				max = gameState[i][1] if gameState[i][1] > max else max
		return max

	def drawTitle(self, firstCol, lastCol):
		line = "-"
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

class ReaderThread(threading.Thread):
	def __init__(self, threadId, name, connection, clientThread):
		threading.Thread.__init__(self)
		self.connection = connection
		self.clientThread = clientThread

	def run(self):
		while True:
			response = self.connection.recv(1024)
			if response == "PING":
				self.connection.send("PONG")
			else:
				self.clientThread.setResponse(response)

# ------------------------Global Variables------------------------
debug = True

# ------------------------Main Program Functionality------------------------
client = Client()
client.connect()
