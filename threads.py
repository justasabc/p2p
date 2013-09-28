from threading import Thread,Event
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
