from xmlrpclib import ServerProxy
from cmd import Cmd
from threading import Thread
from time import sleep
import sys
import socket
# by kzl
from settings import mylogger,NOT_EXIST,ACCESS_DENIED,SUCCESS,PORT,SHARED_FOLDER,SERVER_START_TIME,SECRET_LENGTH,IPS_FILE
from utils import randomstring,generate_urls
from p2p_server import ListableNode

class Client(Cmd):
	"""
	a simple client like cmd
	"""
	prompt = '>'
	
	def __init__(self,port,dirname,ipsfile):
		Cmd.__init__(self)
		self.secret = randomstring(SECRET_LENGTH)
		# start node server in a seprate thread
		n = ListableNode(port,dirname,self.secret)
		# node's start method may throw exception
		t = Thread(target=n._start)
		# true: thread stopped once main thread exit
		# false: thread still run when main thread exit, then we have to CRLT+Z to stop thread running
		t.setDaemon(1)
		t.start()
		# force main thread to sleep until node server is started
		sleep(SERVER_START_TIME)
		# if node server not running ,the exit
		if not n.running:
			sys.exit()
		self.server = ServerProxy(n.url,allow_none=True)
		# add other to myself
		for url in generate_urls(ipsfile):
			self.server.addurl(url)
		# inform others that myself is online
		# add myself to others
		self.server.inform(True)
	
	def do_fetch(self,arg):
		if not arg:return
		print('###[do_fetch]: begin')
		code= self.server.fetch(arg,self.secret)
		if code == SUCCESS:
			print("###[do_fetch]: Fetch file successfully")
		elif code == ACCESS_DENIED:
			print("###[do_fetch]: Access denied")
		else:
			print("###[do_fetch]: File not exist")

	def do_list(self,arg):
		print('###[do_list]: shared files in this node')
		print(self.server.list())

	def do_exit(self,arg):
		# inform others that myself is offline
		self.server.inform(False)
		sys.exit()

	do_EOF = do_exit;

def main():
	client = Client(PORT,SHARED_FOLDER,IPS_FILE)
	client.cmdloop()

if __name__ =='__main__':
	main()
