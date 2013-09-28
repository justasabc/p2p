from xmlrpclib import ServerProxy
from cmd import Cmd
from os.path import join
import thread
from threading import Thread,Event
from time import sleep
import sys
import socket
import argparse
import logging
# by kzl
from settings import mylogger,NOT_EXIST,ACCESS_DENIED,ALREADY_EXIST,SUCCESS,PORT,SHARED_FOLDER,SERVER_START_TIME,SECRET_LENGTH,IPS_FILE
from utils import randomstring,generate_urls
from p2p_server import ListableNode
# gui
from PyQt4 import QtGui,QtCore
from settings import WIN_WIDTH,WIN_HEIGHT,ICON_APP,ICON_FETCH,ICON_QUIT

class NodeServerThread(Thread):
	"""
	thread for starting and stopping node server
	"""
	def __init__(self,name,port,dirname,secret,event_running):
		super(NodeServerThread,self).__init__()
		self.name = name
		self.daemon = True
		self.port = port
		self.dirname = dirname
		self.secret = secret
		self.event_running = event_running
		# server_node
		self.server_node = None
		
	def run(self):
		mylogger.info('[NodeServerThread]: {0} starting...'.format(self.name))
		self.server_node = ListableNode(self.port,self.dirname,self.secret,self.event_running)
		# start node server
		self.server_node._start()

	def stop(self):
		mylogger.info('[NodeServerThread] {0} stopping ...'.format(self.name))
		# shutdown node server
		self.server_node._shutdown()
		mylogger.info('[NodeServerThread] {0} stopped'.format(self.name))

class NodeService():
	"""
	node service: start stop list listall fetch 
	"""	
	def __init__(self,port,dirname,ipsfile):
		self.port = port
		self.dirname = dirname
		self.secret = randomstring(SECRET_LENGTH)
		self.ipsfile = ipsfile
		# indicate whether node server is running
		self.event_running= Event() # flag is false by default
		# server thread instance
		self.server_thread = NodeServerThread('Thread-SERVER',self.port,self.dirname,self.secret,self.event_running)
		# node server proxy for client use
		self.server = None

	def _getfilepath(self,query):
		# query like  './share/11.txt' or '11.txt'
		if query.startswith(self.dirname):
			return query
		else:
			return join(self.dirname,query)

	"""
	start NodeServerThread in child thread,and connect to server in main thread 
	"""
	def start(self):
		mylogger.info('[start]: NodeService starting...')
		# 1)start node server in child thread
		self.server_thread.start()
		# 2) connect to server in main thread
		# block current thread until node server is started
		if not self.event_running.wait(3):
			sys.exit()
		mylogger.info('[start]: NodeServerThread started') 
		mylogger.info('[start]: Connecting to server in Main Thread...')
		# get url from server_node
		url = self.server_thread.server_node.url
		self.server = ServerProxy(url,allow_none=True)
		mylogger.info('[start]: Connected to server in Main Thread')
		# add others to myself
		for url in generate_urls(self.ipsfile):
			self.server.add(url)
		# inform others that myself is online
		# add myself to others
		self.server.inform(True)
		mylogger.info('[start]: NodeService started')

	def stop(self):
		mylogger.info('[stop]: NodeService stopping...')
		# 1)inform others that myself is offline
		self.server.inform(False)
		# 2)stop node server thread
		self.server_thread.stop()
		mylogger.info('[stop]: NodeService stopped')

	"""
	node server methods
	"""
	def fetch(self,query):
		# fetch file from available node
		filepath = self._getfilepath(query)
		return self.server.fetch(filepath,self.secret)

	def list(self):
		# list files in local node
		return self.server.list()

	def listall(self):
		# list files in all nodes
		return self.server.listall()
	
	def geturl(self):
		# get url of local node
		return self.server.geturl()


class GuiWidget(QtGui.QWidget):
	"""
	gui widget: 
	"""	
	def __init__(self,parent):
		super(GuiWidget,self).__init__(parent)
		self.initUI()

	def initUI(self):
		# controls and layouts
		hbox1 = QtGui.QHBoxLayout()
		self.le = QtGui.QLineEdit()
		self.btn = QtGui.QPushButton('Fetch')
		hbox1.addWidget(self.le)
		hbox1.addWidget(self.btn)
		
		vbox1 = QtGui.QVBoxLayout()
		self.label_local = QtGui.QLabel('local')
		self.list_local = QtGui.QListWidget()
		vbox1.addWidget(self.label_local)
		vbox1.addWidget(self.list_local)
		
		vbox2 = QtGui.QVBoxLayout()
		self.label_remote = QtGui.QLabel('remote')
		self.list_remote = QtGui.QListWidget()
		vbox2.addWidget(self.label_remote)
		vbox2.addWidget(self.list_remote)
		
		hbox2 = QtGui.QHBoxLayout()
		hbox2.addLayout(vbox1)
		hbox2.addLayout(vbox2)

		vbox = QtGui.QVBoxLayout(self)
		vbox.addLayout(hbox1)
		vbox.addLayout(hbox2)
	
		# set layout
		self.setLayout(vbox)

class GuiClient(NodeService,QtGui.QMainWindow):
	"""
	a simple client with gui
	"""
	def __init__(self,port,dirname,ipsfile):
		NodeService.__init__(self,port,dirname,ipsfile)
		QtGui.QMainWindow.__init__(self)
		# start node service
		NodeService.start(self)
		# init params
		self.initParams()
		# init gui
		self.initUI()

	def initParams(self):
		self.localurl = NodeService.geturl(self)
		self.listfiles_local = []
		self.listfiles_remote = []

	def initUI(self):
		mylogger.info("[initUI]...")
		# menus toolbars statusbar
		# actions
		self.fetchAction = QtGui.QAction(QtGui.QIcon(ICON_FETCH), '&Fetch', self)
		self.fetchAction.setShortcut('Ctrl+F')
		self.fetchAction.setStatusTip('Fetch file')
		self.fetchAction.triggered.connect(self.onFetchHandler)

		self.stopAction = QtGui.QAction(QtGui.QIcon(ICON_QUIT), '&Quit', self)
		self.stopAction.setShortcut('Ctrl+Q')
		self.stopAction.setStatusTip('Quit application')
		self.stopAction.triggered.connect(self.close)

		menubar = self.menuBar()
		fileMenu = menubar.addMenu('&File')
		fileMenu.addAction(self.fetchAction)
		fileMenu.addAction(self.stopAction)
		
		toolbar = self.addToolBar('tool')
		toolbar.addAction(self.fetchAction)
		toolbar.addAction(self.stopAction)
	
		self.statusbar = self.statusBar()
		# GuiWidget 
		self.main_widget = GuiWidget(self)
		self.main_widget.le.textChanged[str].connect(self.onTextChanged)
		self.main_widget.btn.clicked.connect(self.onFetchHandler)
		self.main_widget.list_remote.itemClicked.connect(self.onListItemClicked)
		# set central widget for main window
		self.setCentralWidget(self.main_widget)

		# set control states
		self.setFetchEnabled(False)
		# update list
		self.updateList()

		# settings for window
		self.resize(WIN_WIDTH,WIN_HEIGHT)
		#self.move(200,200)
		self.center()
		self.setWindowTitle('File Sharing Client')
		self.setWindowIcon(QtGui.QIcon(ICON_APP))
		self.show()

	def _updateLocalList(self):
		mylogger.info("[_updateLocalList]...")
		self.main_widget.list_local.clear()
		for f in self.listfiles_local:
			self.main_widget.list_local.addItem(f)

	def _updateRemoteList(self):
		mylogger.info("[_updateRemoteList]...")
		self.main_widget.list_remote.clear()
		for f in self.listfiles_remote:
			self.main_widget.list_remote.addItem(f)
	
	def updateList(self):
		mylogger.info("[updateList]...")
		for url,lst in NodeService.listall(self):
			if self.localurl == url:
				self.listfiles_local = lst
			else:
				self.listfiles_remote.extend(lst)
		self._updateLocalList()
		self._updateRemoteList()

	def setFetchEnabled(self,enabled):
		self.fetchAction.setEnabled(enabled)
		self.main_widget.btn.setEnabled(enabled)

	def center(self):
		mbr = self.frameGeometry()
        	cen = QtGui.QDesktopWidget().availableGeometry().center()
        	mbr.moveCenter(cen)
        	self.move(mbr.topLeft())

	def keyPressEvent(self,event):	
		mylogger.info("[keyPressEvent]")
		if event.key() == QtCore.Qt.Key_Escape:
			self.close()
		elif event.key() == QtCore.Qt.Key_Enter:
			self.onFetchHandler(False)
		else: pass
	
	def closeEvent(self,event):
		mylogger.info("[closeEvent]")
		# If we close the QtGui.QWidget, the QtGui.QCloseEvent is generated and closeEvent is called.
        	reply = QtGui.QMessageBox.question(self, 'Message', "Are you sure to stop?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes) 
        	if reply == QtGui.QMessageBox.Yes:
			# when exit,inform other nodes 
			msg = ('###[closeEvent]: program is going to exit... ')
			mylogger.info(msg)
			print(msg)
			NodeService.stop(self)
            		event.accept()
       		else:
            		event.ignore()        

	def onTextChanged(self,value):
		if value.isEmpty():
			# set control states
			self.setFetchEnabled(False)
		else:
			# set control states
			self.setFetchEnabled(True)
		
	def onFetchHandler(self,value):
		mylogger.info("[onFetchHandler]")
		# by default ,for a button value is False
		arg = str(self.main_widget.le.text())
		if not arg.strip():
			msg = 'Please enter query file'
			self.statusbar.showMessage(msg)
			return
		# add statusbar messge for fetching file
		msg = "Fetching [{0}].......".format(arg)
		mylogger.info(msg)
		self.statusbar.showMessage(msg)
		# use NodeService
		code = NodeService.fetch(self,arg)
		if code == SUCCESS:
			msg ="Fetch successfully for [{0}]".format(arg)
			self._onFetchSuccessfully(arg)
		elif code == ACCESS_DENIED:
			msg ="Access denied for [{0}]".format(arg)
		elif code == NOT_EXIST:
			msg ="Not exist for [{0}]".format(arg)
		else:
			msg = "Already exist for [{0}]".format(arg)
		mylogger.info(msg)
		self.statusbar.showMessage(msg)
	
	def _onFetchSuccessfully(self,arg):
		# when fetch successfully, need to update local list
		# update local list
		filepath = NodeService._getfilepath(arg) 
		self.listfiles_local.append(filepath)
		self.main_widget.list_local.addItem(filepath)
		# self._updateLocalList()

	def onListItemClicked(self,value):
		self.main_widget.le.setText(value.text())
		self.statusbar.showMessage('')
		
def main_gui():
	app = QtGui.QApplication(sys.argv)
	client = GuiClient(PORT,SHARED_FOLDER,IPS_FILE)
	sys.exit(app.exec_())

class ConsoleClient(NodeService,Cmd):
	"""
	a simple console client
	"""
	prompt = '>'

	def __init__(self,port,dirname,ipsfile):
		NodeService.__init__(self,port,dirname,ipsfile)
		Cmd.__init__(self)
		# start node service
		NodeService.start(self)

	def do_fetch(self,arg):
		"""
		fetch <filename>
		"""
		if not arg or not arg.strip():
			msg = '###[do_fetch]: Please enter file name'
			print(msg)
			return
		code = NodeService.fetch(self,arg)
		if code == SUCCESS:
			msg ="###[do_fetch]: Fetch successfully for [{0}]".format(arg)
		elif code == ACCESS_DENIED:
			msg ="###[do_fetch]: Access denied for [{0}]".format(arg)
		elif code == NOT_EXIST:
			msg ="###[do_fetch]: Not exist for [{0}]".format(arg)
		else:
			msg = "###[do_fetch]: Already exist for [{0}]".format(arg)
		print(msg)

	def do_list(self,arg):
		"""
		list all shared files in local node	
		"""
		print('###[do_list]: list shared files in local node')
		for f in NodeService.list(self):
			print(f)

	def do_listall(self,arg):
		"""
		list shared files in all remote nodes	
		"""
		print('###[do_listall]: list shared files in all remote nodes')
		for url,lt in NodeService.listall(self):
			print('*'*60)
			print('url:{0}'.format(url))
			print('files:')
			for f in lt:
				print(f)

	def do_geturl(self,arg):
		"""
		get url of local node
		"""
		print('###[do_geturl]: get url of local node')
		print(NodeService.geturl(self))

	def do_exit(self,arg):
		"""
		exit or quit program
		"""
		print('###[do_exit]: program is going to exit... ')
		NodeService.stop(self)
		sys.exit()

	do_EOF = do_quit = do_exit;

def main_console():
	client = ConsoleClient(PORT,SHARED_FOLDER,IPS_FILE)
	client.cmdloop()

# argparse
parser = argparse.ArgumentParser(description='p2p node application')
'''
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action="store_true",help="output detail to console")
group.add_argument("-q", "--quiet", action="store_true",help="output detail to log file")
'''
group_mode = parser.add_mutually_exclusive_group()
group_mode.add_argument("-c", "--console",action="store_true", help = "run application in console mode" )
group_mode.add_argument("-g", "--gui", action = "store_true", help="run application in gui mode")
args = parser.parse_args()

if __name__ =='__main__':
	if args.console:
		main_console()
	else: # args.gui
		main_gui()
