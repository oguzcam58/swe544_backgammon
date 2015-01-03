#!/usr/bin/env python
import socket # Import socket module

class Client:
	def __init__(self):
		self.clientSocket = socket.socket() # Create a socket object
		self.host = socket.gethostname() # Get local machine name
		self.port = 12345 # Reserve a port for your service.

	def connect(self):
		self.clientSocket.connect((self.host, self.port))

client = Client()
client.connect()