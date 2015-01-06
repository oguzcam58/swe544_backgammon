#!/usr/bin/env python
import socket # Import socket module

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
					self.clientParser(response)
					break
		# Quit
		self.clientSocket.close()

	def clientParser(self, response):
		if response != None:
			responseParsed = response.split("#")
			if responseParsed:
				print(responseParsed)

debug = True

client = Client()
client.connect()
