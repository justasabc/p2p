from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy,Fault
from os.path import join,abspath,isfile
from urlparse import urlparse
import sys
import socket

SimpleXMLRPCServer.allow_reuse_address = 1
MAX_HISTORY_LENGTH = 6

NOT_EXIST = -1
ACCESS_DENIED = 0
SUCCESS = 1

'''
class NotExist(Fault):
	"""
	excption raised when requested file does not exist
	"""
	def __init__(self,message='Can not find the file'):
		Fault.__init__(self,NOT_EXIST,message)

class AccessDenied(Fault):
	"""
	excption raised when requested file is access denied
	"""
	def __init__(self,message='Access denied'):
		Fault.__init__(self,ACCESS_DENIED,message)
'''

def inside(dirname,filename):
	"""
	check whether filename exists in dir folder 
	"""
	absdir = abspath(dirname)
	absfile = abspath(filename)
	return absfile.startswith(join(absdir,''))

def getport(url):
	"""
	get port number from url like http://localhost:5555
	"""
	name = urlparse(url)[1] # localhost:5555
	parts = name.split(':')
	return int(parts[-1])
	
class Node:
	"""
	a simple node class
	"""
	def __init__(self,url,dirname,secret):
		self.url = url
		self.dirname = dirname
		self.secret = secret
		# store all known urls in set (including self)
		self.known = set()
		# store un reachable urls
		self.unreachable = set()
	
	def hello(self,other):
		print("[hello]: {0}".format(other))
		self.known.add(other)
		return SUCCESS
	
	def query(self,query,history=[]):
		# return value:(NOT_EXIST,None)(ACCESS_DENIED,None)(SUCCESS,data)
		print('-'*40)
		print('[query]: querying from {0}'.format(self.url))
		code,data = self._handle(query)
		if code == SUCCESS:
			print('[query]: success')
			return code,data
		elif code == NOT_EXIST:
			# history is a list containing urls from which we can not find file
			history = history + [self.url]
			if len(history)>MAX_HISTORY_LENGTH:
				print('[query]: history too long')
				return NOT_EXIST,None
			print("[query]: query for {0} NOT in {1}".format(query,history))
			#return self._broadcast(query,history)
			code,data = self._broadcast(query,history)
			print("[query]: [after broadcast]: {0}".format(code))
			print("[query]: knows: {0}".format(self.known))
			print("[query]: unreachable: {0}".format(self.unreachable))
			return code,data
		else: # access denied
			return code,data
	def fetch(self,query,secret):
		print('-'*60)
		print('[fetch]: fetching from {0}'.format(self.url))
		if secret != self.secret:
			return ACCESS_DENIED
		code,data = self.query(query) 
		print('[fetch]: query return code {0}'.format(code))
		print("[fetch]: knows: {0}".format(self.known))
		print("[fetch]: unreachable: {0}".format(self.unreachable))
		if code == SUCCESS:
			f = open(join(self.dirname,query),'w')
			f.write(data)
			f.close()
		return code

	def _start(self):
		try:
			t = ('',getport(self.url))
			# in both server and client set allow_none=True
			s = SimpleXMLRPCServer(t,allow_none=True,logRequests=False)
			s.register_instance(self)
			print("Server started at {0}".format(self.url))
			s.serve_forever()
		except:
			print('Server failed to start at {0}'.format(self.url))
			sys.exit()

	def _handle(self,query):
		print('-'*20)
		print('[handle]: begin')
		dir = self.dirname
		filepath = join(dir,query)
		print(filepath)
		if not isfile(filepath):
			print('[handle]: not file')
			return NOT_EXIST,None
		if not inside(dir,filepath):
			print('[handle]: not inside')
			return ACCESS_DENIED,None
		print('[handle]: success')
		return SUCCESS,open(filepath).read()

	def _broadcast(self,query,history):
		print('-'*10)
		print('[broadcast]:')
		print("knows: {0}".format(self.known))
		print("unreachable: {0}".format(self.unreachable))
		print("history: {0}".format(history))
		#for other in self.known.copy()-self.unreachable.copy():
		for other in self.known.copy():
			print('[broadcast]: other is {0}'.format(other))
			if other in history or other in self.unreachable.copy():
				continue
			s = ServerProxy(other)
			print('[broadcast]: Connecting from {0} to {1}'.format(self.url,other))
			print('*'*80)
			try:
				code,data = s.query(query,history)
				print('[broadcast]: query return code {0}'.format(code))
				if code == SUCCESS:
					print('[broadcast]: query SUCCESS!!!')
					return code,data
				elif code == NOT_EXIST:
					print('[broadcast]: query NOT_EXIST!!!')
				else:
					print('[broadcast]: query ACCESS_DENIED!!!')
			except Fault, f: # connected to server,but method does not exist(Never happen in this example)
				print("[EXCEPT]:fault")
				print(f)
			except socket.error, e:
				print("[EXCEPT]:socket error")
				print(e)
				print('[broadcast]: CAN NOT connect from {0} to {1}'.format(self.url,other))
				# added by kzl
				self.known.remove(other)
				self.unreachable.add(other)
				print('[broadcast]: <knows>: {0}'.format(self.known))
				print("[broadcast]: <history>: {0}".format(history))
				print("[broadcast]: <unreachable>: {0}".format(self.unreachable))
				#continue; # Notice here
			except Exception, e:
				print("[EXCEPT]: Exception")
				print(e)
		print('[broadcast] not found')
		return NOT_EXIST,None


def main():
	if len(sys.argv)<4:
		print('Usage: python xxx.py url dir secret')
		sys.exit()
	else:
		url,directory,secret = sys.argv[1:]
		n = Node(url,directory,secret)
		n._start()

if __name__ =='__main__':
	main()
