#!/usr/bin/env python
import socket # Import socket module

# ------------------------Client------------------------
class Client:
	def __init__(self):
		self.clientSocket = socket.socket() # Create a socket object
		self.host = socket.gethostname() # Get local machine name
		self.port = 12345 # Reserve a port for your service.

	def connect(self):
		self.clientSocket.connect((self.host, self.port))
		while True:
			request = raw_input("Say something")
			self.clientSocket.send(request)
			while True:
				response = self.clientSocket.recv(1024)
				if response:
					isWait = self.clientParser(response)
					if not isWait:
						break
		# Quit
		self.clientSocket.close()

	def clientParser(self, response):
		isWait = False
		if response != None:
			responseParsed = response.split("#")
			if len(responseParsed) > 1:
				if (responseParsed[0] == "NEGR" or responseParsed[0] == "WAGR"):
					isWait = True

			if responseParsed:
				print(responseParsed[len(responseParsed) - 1])
		return isWait


# ------------------------Global Variables------------------------
debug = True


# ------------------------Main Program Functionality------------------------
client = Client()
client.connect()
