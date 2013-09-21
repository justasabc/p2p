from xmlrpclib import ServerProxy
from cmd import Cmd
from random import choice
from string import lowercase
from p2p_server import Node,NOT_EXIST,ACCESS_DENIED,SUCCESS
from threading import Thread
from time import sleep
import sys
import logging
import argparse

#logging.basicConfig(level = logging.DEBUG)
logging.basicConfig(filename='p2p.log',level = logging.DEBUG)
#logging.basicConfig(filename='p2p.log',level=logging.DEBUG,format='%(lev        elname)s %(asctime)s %(message)s')
mylogger = logging.getLogger('xxx')

# argparse
parser = argparse.ArgumentParser(description='p2p node')
group = parser.add_mutually_exclusive_group()
group.add_argument("-q", "--quiet", action="store_true",help="not output inf    o to console")
group.add_argument("-v", "--verbose", action="store_true",help="output detai    led info to console")
parser.add_argument("url", type=str, help="set url of this node; for exam    ple: http://localhost:1111")
parser.add_argument("dir", type=str, help="set shared directory of this node; for example: folder1/")
parser.add_argument("urlfile", type=str, help="set path to urlfile containing all known urls")
args = parser.parse_args()
url = args.url
directory = args.dir
urlfile = args.urlfile
if args.verbose:
        mylogger = logging
	print(mylogger)
#print(url,directory,urlfile)

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
		# true: thread stopped once main thread exit
		# false: thread still run when main thread exit, then we have to CRLT+Z to stop thread running
		t.setDaemon(1) 
		t.start()
		# force main thread to sleep until node server is started
		sleep(SERVER_START_TIME)
		self.server = ServerProxy(url,allow_none=True)
		# add other to myself
		for line in open(urlfile):
			line = line.strip()
			# add urls to known url set
			self.server.addurl(line)
		# inform others that myself is online
		self.server.inform(True)

	def do_fetch(self,arg):
		if not arg:
			return
		print('###[do_fetch]: begin')
		code= self.server.fetch(arg,self.secret)
		if code == SUCCESS:
			print("###[do_fetch]: Fetch file successfully")
		elif code == ACCESS_DENIED:
			print("###[do_fetch]: Access denied")
		else:
			print("###[do_fetch]: File not exist")

	def do_exit(self,arg):
		# inform others that myself is offline
		self.server.inform(False)
		sys.exit()

	do_EOF = do_exit;

def main():
	#url,directory,urlfile = sys.argv[1:]
	client = Client(url,directory,urlfile)
	client.cmdloop()

if __name__ =='__main__':
	main()
