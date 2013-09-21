from xmlrpclib import ServerProxy
from cmd import Cmd
from random import choice
from string import lowercase
from p2p_server import Node,NOT_EXIST,ACCESS_DENIED,SUCCESS
from threading import Thread
from time import sleep
import sys

SERVER_START_TIME = 0.1
SECRET_LENGTH = 100

def randomstring(length):
	"""
	generate a random string for given length
	"""
	chars = []
	letters = lowercase[:26]
	while length>0:
		length -=1
		chars.append(choice(letters))
	return ''.join(chars)

class Client(Cmd):
	"""
	a simple client like cmd
	"""
	prompt = '>'
	
	def __init__(self,url,dirname,urlfile):
		Cmd.__init__(self)
		self.secret = randomstring(SECRET_LENGTH)
		# start node server in a seprate thread
		n = Node(url,dirname,self.secret)
		t = Thread(target=n._start)
		t.setDaemon(1)
		t.start()
		# force main thread to sleep until node server is started
		sleep(SERVER_START_TIME)
		print('###[init]: connecting to {0}'.format(url))
		self.server = ServerProxy(url,allow_none=True)
		for line in open(urlfile):
			line = line.strip()
			# add urls to known url set
			self.server.hello(line)

	def do_fetch(self,arg):
		print('###[do_fetch]: begin')
		code= self.server.fetch(arg,self.secret)
		if code == SUCCESS:
			print("###[do_fetch]: Fetch file successfully")
		elif code == ACCESS_DENIED:
			print("###[do_fetch]: Access denied")
		else:
			print("###[do_fetch]: File not exist")

	def do_exit(self,arg):
		print
		sys.exit()

	do_EOF = do_exit;

def main():
	url,directory,urlfile = sys.argv[1:]
	client = Client(url,directory,urlfile)
	client.cmdloop()

if __name__ =='__main__':
	main()
