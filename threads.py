from threading import Thread,Event
import time
from settings import mylogger
import files

class SaveFileThread(Thread):
	"""
	background(daemon) thread for save file
	"""
	def __init__(self,name,filepath,data):
		mylogger.info('[SaveFileThread]:Init...' )
		super(SaveFileThread,self).__init__()
		self.name = name
		self.daemon = True
		self.filepath = filepath
		self.data = data

	def run(self):
		mylogger.info('[SaveFileThread]: Starting {0}'.format(self.name))
		mylogger.info('[SaveFileThread]: Saving to {0} ...'.format(self.filepath))
		t1 = time.clock()
		files.savefile_frombinary_xmlrpc(self.filepath,self.data)
		mylogger.info('[SaveFileThread]: Time used {0}s'.format(time.clock()-t1))
		mylogger.info('[SaveFileThread]: Exiting {0}'.format(self.name))


class SaveIPsThread(Thread):
	"""
	background(daemon) thread for save ips to file
	"""
	def __init__(self,name,target):
		mylogger.info('[__init__]: {0}'.format(name))
		super(SaveIPsThread,self).__init__()
		self.name = name
		self.daemon = True
		self.target = target

	def run(self):
		mylogger.info('[SaveIPsThread]: Starting {0}'.format(self.name))
		# call target
		self.target()
		mylogger.info('[SaveIPsThread]: Exiting {0}'.format(self.name))


class UpdateGUIListTimer(Thread):
	"""
	background(daemon) thread for update gui local and remote list
	in n seconds
	"""
	def __init__(self,name,interval,target):
		mylogger.info('[__init__]: {0}'.format(name))
		super(UpdateGUIListTimer,self).__init__()
		self.name = name
		self.daemon = True
		self.interval = interval
		self.target = target
		# whether to stop thread
		self.stopped = Event() # default false

	def run(self):
		while not self.stopped.is_set():
		#while not self.stopped.wait(self.interval):
			self.stopped.wait(self.interval)
			# call target every interval seconds
			self.target()

	def stop(self):
		self.stopped.set() #set true to stop thread
