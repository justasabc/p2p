from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy,Fault,Binary
from os.path import isfile
import sys
import time
import socket
import thread
from threading import Thread,Event
# by kzl
from settings import mylogger,MAX_HISTORY_LENGTH,NOT_EXIST,ACCESS_DENIED,ALREADY_EXIST,SUCCESS,URL_PREFIX,PORT
from utils import inside,getport,read_urls,save_urls
from files import list_all_files,savefile_frombinary_xmlrpc,readfile_asbinary_xmlrpc
from threads import SaveFileThread

class FileInfo():
	"""
	class for storing file info
	"""
	def __init__(self,filename,filepath,filesize,filedate):
		self.filename = filename
		self.filepath = filepath
		self.filesize = filesize
		self.filedate = filedate

class Node:
	"""
	a simple node class
	"""
	def __init__(self,url,dirname,secret,event_running,ipsfile):
		self.url = url
		self.dirname = dirname
		self.secret = secret
		# store all known urls in set (including self)
		self.known = set()
		# indicate whether node server is running
		self.event_running = event_running
		# ipsfile for storing all available nodes
		self.ipsfile = ipsfile
		# store local node server for later shutdown
		self.local_server = None

	def _read(self):
		"""
		read urls from ipsfile
		"""
		mylogger.info('[_read]: reading urls ... ')
		for url in read_urls(self.ipsfile):
			self.known.add(url)
		mylogger.info('[_read]: reading urls finiehed')

	def _save(self):
		"""
		save urls to ipsfile
		"""
		mylogger.info('[_save]: saving urls ... ')
		save_urls(self.known,self.ipsfile)
		mylogger.info('[_save]: saving urls finiehed')

	def _start(self):
		"""
		start node server
		"""
		try:
			# on start up ,read urls
			self._read()
			t = ('',getport(self.url))
			# in both server and client set allow_none=True
			self.local_server = SimpleXMLRPCServer(t,allow_none=True,logRequests=False)
			self.local_server.register_instance(self)
			msg ="[_start]: Server started at {0}...".format(self.url)
			print(msg)
			mylogger.info(msg)
			self.event_running.set() # set flag to true
			self.local_server.serve_forever()
		except socket.error,e:
			mylogger.warn(e)
			mylogger.warn('[_start]: socket error')
			mylogger.warn('[_start]: program is going to exit...')
			# event_running must be false
		except Exception, e:
			mylogger.warn(e)
			mylogger.warn('[_start]: except')
			mylogger.warn('[_start]: Server stopped at {0}'.format(self.url))
			# event_running must be false

	def _shutdown(self):
		"""
		shut down node server
		"""
		mylogger.warn('[_shutdown]: shutdown server...')
		# on shutdown,save urls
		self._save()
		self.local_server.shutdown()

	def add(self,other):
		"""
		add other to myself's known set
		"""
		mylogger.info('[add]: hello {0}'.format(other))
		self.known.add(other)
		return SUCCESS

	def remove(self,other):
		"""
		remove other from myself's known set
		"""
		mylogger.info('[remove]: byebye {0}'.format(other))
		self.known.remove(other)
		return SUCCESS

	
	def fetch(self,query,secret):
		"""
		fetch a given file from all available nodes
		query:  filepath
		"""
		mylogger.info('-'*60)
		mylogger.info('[fetch]: fetching from {0}'.format(self.url))
		if secret != self.secret:
			return ACCESS_DENIED
		code,data = self.query(query,self.url,[]) 
		mylogger.info('[fetch]: query return code {0}'.format(code))
		mylogger.info("[fetch]: knows: {0}".format(self.known))
		if code == SUCCESS:
			# create a background(daemon) thread to save file
			thread = SaveFileThread('Thread-savefile',query,data)
			thread.start()
		return code

	def query(self,query,starturl,history=[]):
		"""
		query a given file
		return value:(NOT_EXIST,None)(ACCESS_DENIED,None)(ALREADY_EXIST,None)(SUCCESS,data)
		"""
		mylogger.info('-'*40)
		mylogger.info('[query]: querying from {0}'.format(self.url))
		code,data = self._handle(query,starturl)
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
			code,data = self._broadcast(query,starturl,history)
			mylogger.info("[query]: [after broadcast]: {0}".format(code))
			mylogger.info("[query]: knows: {0}".format(self.known))
			return code,data
		else: # access denied or already exist
			return code,data

	def _handle(self,query,starturl):
		"""
		handle query in local node
		# query like  './share/11.txt' 
		"""
		mylogger.info('-'*20)
		mylogger.info('[handle]: begin')
		filepath = query # query is filepath
		mylogger.info('[handle]: filepath is {0}'.format(filepath))
		if not isfile(filepath):
			mylogger.info('[handle]: not file')
			return NOT_EXIST,None
		if not inside(self.dirname,filepath):
			mylogger.info('[handle]: not inside')
			return ACCESS_DENIED,None
		if starturl == self.url:
			mylogger.info('[handle]: ******already exist******')
			return ALREADY_EXIST,None
		mylogger.info('[handle]: success')
		mylogger.info('[handle]: reading {0} ...'.format(filepath))
		t1 = time.clock()
		data = readfile_asbinary_xmlrpc(filepath)
		mylogger.info('[handle]: reading finished'.format(filepath))
		mylogger.info('[handle]: time used {0}s'.format(time.clock()-t1))
		return SUCCESS,data

	def _broadcast(self,query,starturl,history):
		"""
		broadcast to all other nodes
		"""
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
				code,data = s.query(query,starturl,history)
				mylogger.info('[broadcast]: query return code {0}'.format(code))
				if code == SUCCESS:
					mylogger.info('[broadcast]: query SUCCESS!!!')
					return code,data
				elif code == NOT_EXIST:
					mylogger.info('[broadcast]: query NOT_EXIST!!!')
				else:
					mylogger.info('[broadcast]: query ACCESS_DENIED!!!')
			except Fault, f: # connected to server,but method does not exist(Never happen in this example)
				mylogger.warn(f)
				mylogger.warn("[broadcast]:except fault")
			except socket.error, e:
				mylogger.warn(e)
				mylogger.warn("[broadcast]:except socket error")
				mylogger.warn('[broadcast]: CAN NOT connect from {0} to {1}'.format(self.url,other))
				# added by kzl
				self.known.remove(other)
				#mylogger.warn('[broadcast]: <knows>: {0}'.format(self.known))
				#mylogger.warn("[broadcast]: <history>: {0}".format(history))
			except Exception, e:
				mylogger.warn(e)
				mylogger.warn("[broadcast]: Exception")
		mylogger.info('[broadcast] not found')
		return NOT_EXIST,None

class ListableNode(Node):
	"""
	node that we can list all available files in dirname
	"""
	def __init__(self,url,dirname,secret,event_running,ipsfile):
		Node.__init__(self,url,dirname,secret,event_running,ipsfile)
		# NEW variables
		self.local_files = []
		self.remote_files = []

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
				# inform other node to add local node url
				s.add(self.url)
				# inform other node to update files list
				#s.listall()
			except Fault,f:
				mylogger.warn(f)
				mylogger.warn('[inform]: {0} started but inform failed'.format(other))
			except socket.error:
				mylogger.warn('[inform]: {0} not started'.format(other))
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
				# inform other node to remove local node url
				s.remove(self.url)
				# inform other node to update files list
				#s.listall()
			except Fault,f:
				mylogger.warn(f)
				mylogger.warn('[inform]: {0} started but inform failed'.format(other))
			except socket.error:
				mylogger.warn('[inform]: {0} not started'.format(other))
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

	def list(self):
		"""
		list files in local node
		"""
		mylogger.info('[list]: list files in {0}'.format(self.url))
		if not len(self.local_files):
			self.local_files = list_all_files(self.dirname)
		return self.local_files
	
	def _listother(self,other):
		"""
		list files in other node
		"""
		mylogger.info('[_listother]: list files in {0}'.format(other))
		s = ServerProxy(other)
		lt = []
		try:
			lt = s.list()
		except Fault,f:
			mylogger.warn(f)
			mylogger.warn('[_listother]: {0} started but list failed'.format(other))
		except socket.error,e:
			mylogger.warn(e)
			mylogger.warn('[_listother]: {0} not started'.format(other))
			pass
		return lt

	def listall(self):
		"""
		list all files in known urls: for gui
		"""
		mylogger.info('[listall]: list all files in remote nodes')
		self.local_files = []
		self.remote_files = []
		for other in self.known.copy():
			if other == self.url:
				lt = self.list()
				# update local files
				self.local_files = lt
			else:
				lt = self._listother(other)
				# update remote files
				self.remote_files.extend(lt)
		return self.local_files,self.remote_files

	def listall2(self):
		"""
		list all files in known urls: for console
		"""
		mylogger.info('[listall]: list all files in remote nodes')
		url_list={}
		self.local_files = []
		self.remote_files = []
		for other in self.known.copy():
			if other == self.url:
				lt = self.list()
				# update local files
				self.local_files = lt
			else:
				lt = self._listother(other)
				# update remote files
				self.remote_files.extend(lt)
			url_list[other]= lt
		return url_list.items()

def main():
	n = Node(21111,'share/','',Event(),Event())
	n._start()

if __name__ =='__main__':
	main()
