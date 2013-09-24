from xmlrpclib import ServerProxy
from cmd import Cmd
from threading import Thread
from time import sleep
import sys
import socket
import argparse
import logging
# by kzl
from settings import mylogger,NOT_EXIST,ACCESS_DENIED,SUCCESS,PORT,SHARED_FOLDER,SERVER_START_TIME,SECRET_LENGTH,IPS_FILE
from utils import randomstring,generate_urls
from p2p_server import Node,ListableNode
# gui
from PyQt4 import QtGui,QtCore
from settings import WIN_WIDTH,WIN_HEIGHT,ICON_APP,ICON_FETCH,ICON_QUIT

class NodeService():
	def __init__(self,port,dirname,ipsfile):
		self.port = port
		self.dirname = dirname
		self.ipsfile = ipsfile
		
	def start(self):
		self.secret = randomstring(SECRET_LENGTH)
		# start node server in a seprate thread
		n = ListableNode(self.port,self.dirname,self.secret)
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
		for url in generate_urls(self.ipsfile):
			self.server.addurl(url)
		# inform others that myself is online
		# add myself to others
		self.server.inform(True)

	def fetch(self,query):
		return self.server.fetch(query,self.secret)

	def list(self):
		return self.server.list()

	def listall(self):
		return self.server.listall()

	def stop(self):
		# inform others that myself is offline
		return self.server.inform(False)

class GuiWidget(QtGui.QWidget):
	"""
	gui widget: QLineEdit QPushButton QTextEdit
	"""	
	def __init__(self,parent):
		super(GuiWidget,self).__init__(parent)
		self.initUI()

	def initUI(self):
		# controls and layouts
		self.le = QtGui.QLineEdit()
		self.btn = QtGui.QPushButton('Fetch')
		
		hbox = QtGui.QHBoxLayout()
		hbox.addWidget(self.le)
		hbox.addWidget(self.btn)
		
		self.lb = QtGui.QListWidget()
		
		vbox = QtGui.QVBoxLayout(self)
		vbox.addLayout(hbox)
		vbox.addWidget(self.lb)
	
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
		# init gui
		self.initUI()

	def initUI(self):
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
		self.main_widget.lb.itemClicked.connect(self.onListItemClicked)
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
	
	def updateList(self):
		for item in NodeService.list(self):
			self.main_widget.lb.addItem(item)

	def setFetchEnabled(self,enabled):
		self.fetchAction.setEnabled(enabled)
		self.main_widget.btn.setEnabled(enabled)

	def center(self):
		mbr = self.frameGeometry()
        	cen = QtGui.QDesktopWidget().availableGeometry().center()
        	mbr.moveCenter(cen)
        	self.move(mbr.topLeft())

	def keyPressEvent(self,event):	
		if event.key() == QtCore.Qt.Key_Escape:
			self.close()
		elif event.key() == QtCore.Qt.Key_Enter:
			self.onFetchHandler(False)
		else: pass
	
	def closeEvent(self,event):
		# If we close the QtGui.QWidget, the QtGui.QCloseEvent is generated and closeEvent is called.
        	reply = QtGui.QMessageBox.question(self, 'Message', "Are you sure to stop?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes) 
        	if reply == QtGui.QMessageBox.Yes:
			# when exit,inform other nodes 
			print('###[do_exit]: program is going to exit... ')
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
		# by default ,for a button value is False
		arg = str(self.main_widget.le.text())
		if not arg.strip():
			msg = 'Please enter query file'
			self.statusbar.showMessage(msg)
			return
		code = NodeService.fetch(self,arg)
		if code == SUCCESS:
			msg ="Fetch file successfully"
		elif code == ACCESS_DENIED:
			msg ="Access denied"
		else:
			msg ="File not exist"
		self.statusbar.showMessage(msg)
	
	def onListItemClicked(self,value):
		self.main_widget.le.setText(value.text())
		
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
			msg ="###[do_fetch]: Fetch file successfully"
		elif code == ACCESS_DENIED:
			msg ="###[do_fetch]: Access denied"
		else:
			msg ="###[do_fetch]: File not exist"
		print(msg)

	def do_list(self,arg):
		"""
		list all shared files in local node	
		"""
		print('###[do_list]: list shared files in local node')
		print(NodeService.list(self))

	def do_listall(self,arg):
		"""
		list shared files in all remote nodes	
		"""
		print('###[do_listall]: list shared files in all remote nodes')
		for url,lt in NodeService.listall(self):
			print('*'*60)
			print('url:{0}'.format(url))
			print('files:{0}'.format(lt))

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
