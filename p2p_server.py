from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy,Fault
from os import listdir
from os.path import join,isfile
import sys
import socket
import argparse
# by kzl
from utils import inside,get_lan_ip
from settings import mylogger,MAX_HISTORY_LENGTH,NOT_EXIST,ACCESS_DENIED,SUCCESS,URL_PREFIX,PORT

IP_LAN = get_lan_ip()

class Node:
	"""
	a simple node class
	"""
	def __init__(self,port,dirname,secret):
		# bool to indicate whether node is running
		self.running = False
		self.port = port
		self.url = "{0}{1}:{2}".format(URL_PREFIX,IP_LAN,port)
		self.dirname = dirname
		self.secret = secret
		# store all known urls in set (including self)
		self.known = set()

	def addurl(self,other):
		"""
		add other to myself's known set
		"""
		mylogger.info('[addurl]: hello {0}'.format(other))
		self.known.add(other)
		return SUCCESS

	def removeurl(self,other):
		"""
		remove other from myself's known set
		"""
		mylogger.info('[removeurl]: byebye {0}'.format(other))
		self.known.remove(other)
		return SUCCESS

	def _online(self):
		"""
		inform others about myself's status(on)
		"""
		mylogger.info('[_online]')
		for other in self.known.copy():
			if other == self.url:
				continue
			s = ServerProxy(other)
			try:
				s.addurl(self.url)
			except Fault:
				mylogger.info('[inform]: {0} started but inform failed'.format(other))
			except socket.error:
				#mylogger.info('[inform]: {0} not started'.format(other))
				pass
	
	def _offline(self):
		"""
		inform others about myself's status(off)
		"""
		mylogger.info('[_offline]')
		for other in self.known.copy():
			if other == self.url:
				continue
			s = ServerProxy(other)
			try:
				s.removeurl(self.url)
			except Fault:
				mylogger.info('[inform]: {0} started but inform failed'.format(other))
			except socket.error:
				#mylogger.info('[inform]: {0} not started'.format(other))
				pass
	
	
	def inform(self,status):
		"""
		inform others about myself's status(on or off)
		"""
		mylogger.info('[inform]: status {0}'.format(status))
		if status:
			self._online()
		else:
			self._offline()
		mylogger.info('[inform]: knows {0}'.format(self.known))
		return SUCCESS
	

	def query(self,query,history=[]):
		# return value:(NOT_EXIST,None)(ACCESS_DENIED,None)(SUCCESS,data)
		mylogger.info('-'*40)
		mylogger.info('[query]: querying from {0}'.format(self.url))
		code,data = self._handle(query)
		if code == SUCCESS:
			mylogger.info('[query]: success')
			return code,data
		elif code == NOT_EXIST:
			# history is a list containing urls from which we can not find file
			history = history + [self.url]
			if len(history)>MAX_HISTORY_LENGTH:
				mylogger.info('[query]: history too long')
				return NOT_EXIST,None
			mylogger.info("[query]: query for {0} NOT in {1}".format(query,history))
			#return self._broadcast(query,history)
			code,data = self._broadcast(query,history)
			mylogger.info("[query]: [after broadcast]: {0}".format(code))
			mylogger.info("[query]: knows: {0}".format(self.known))
			return code,data
		else: # access denied
			return code,data
	def fetch(self,query,secret):
		mylogger.info('-'*60)
		mylogger.info('[fetch]: fetching from {0}'.format(self.url))
		if secret != self.secret:
			return ACCESS_DENIED
		code,data = self.query(query) 
		mylogger.info('[fetch]: query return code {0}'.format(code))
		mylogger.info("[fetch]: knows: {0}".format(self.known))
		if code == SUCCESS:
			f = open(join(self.dirname,query),'w')
			f.write(data)
			f.close()
		return code

	def _start2(self):
		"""
		start may throw exception,catch exception in client.py
		"""
		t = ('',self.port)
		# in both server and client set allow_none=True
		s = SimpleXMLRPCServer(t,allow_none=True,logRequests=False)
		s.register_instance(self)
		print("[_start]: Server started at {0}".format(self.url))
		s.serve_forever()

	def _start(self):
		try:
			t = ('',self.port)
			# in both server and client set allow_none=True
			s = SimpleXMLRPCServer(t,allow_none=True,logRequests=False)
			s.register_instance(self)
			print("[_start]: Server started at {0}".format(self.url))
			self.running = True # running
			s.serve_forever()
		except socket.error,e:
			mylogger.warn('[_start]: socket error')
			mylogger.warn(e)
			self.running = False # not running
			sys.exit()
		except Exception, e:
			mylogger.info('[_start]: except')
			mylogger.warn(e)
			mylogger.info('[_start]: Server stopped at {0}'.format(self.url))
			self.running = False # not running
			sys.exit()

	def _handle(self,query):
		mylogger.info('-'*20)
		mylogger.info('[handle]: begin')
		dir = self.dirname
		filepath = join(dir,query)
		mylogger.info(filepath)
		if not isfile(filepath):
			mylogger.info('[handle]: not file')
			return NOT_EXIST,None
		if not inside(dir,filepath):
			mylogger.info('[handle]: not inside')
			return ACCESS_DENIED,None
		mylogger.info('[handle]: success')
		return SUCCESS,open(filepath).read()

	def _broadcast(self,query,history):
		mylogger.info('-'*10)
		mylogger.info('[broadcast]:')
		mylogger.info("knows: {0}".format(self.known))
		mylogger.info("history: {0}".format(history))
		for other in self.known.copy():
			mylogger.info('[broadcast]: other is {0}'.format(other))
			if other in history:
				continue
			s = ServerProxy(other)
			mylogger.info('[broadcast]: Connecting from {0} to {1}'.format(self.url,other))
			mylogger.info('*'*80)
			try:
				code,data = s.query(query,history)
				mylogger.info('[broadcast]: query return code {0}'.format(code))
				if code == SUCCESS:
					mylogger.info('[broadcast]: query SUCCESS!!!')
					return code,data
				elif code == NOT_EXIST:
					mylogger.info('[broadcast]: query NOT_EXIST!!!')
				else:
					mylogger.info('[broadcast]: query ACCESS_DENIED!!!')
			except Fault, f: # connected to server,but method does not exist(Never happen in this example)
				mylogger.info("[broadcast]:except fault")
				mylogger.info(f)
			except socket.error, e:
				mylogger.info("[broadcast]:except socket error")
				mylogger.info(e)
				mylogger.info('[broadcast]: CAN NOT connect from {0} to {1}'.format(self.url,other))
				# added by kzl
				self.known.remove(other)
				mylogger.info('[broadcast]: <knows>: {0}'.format(self.known))
				mylogger.info("[broadcast]: <history>: {0}".format(history))
			except Exception, e:
				mylogger.info("[broadcast]: Exception")
				mylogger.info(e)
		mylogger.info('[broadcast] not found')
		return NOT_EXIST,None


class ListableNode(Node):
	"""
	node that we can list all available files in dirname
	"""

	def __init(self):
		Node.__init__()

	def list(self):
		return listdir(self.dirname)

def main():
	n = Node(21111,'share/','')
	n._start()

if __name__ =='__main__':
	main()
