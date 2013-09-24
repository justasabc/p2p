from xmlrpclib import ServerProxy
from cmd import Cmd
from threading import Thread
from time import sleep
import sys
import socket
# gui
from PyQt4 import QtGui,QtCore
# by kzl
from settings import mylogger,NOT_EXIST,ACCESS_DENIED,SUCCESS,PORT,SHARED_FOLDER,SERVER_START_TIME,SECRET_LENGTH,IPS_FILE
from utils import randomstring,generate_urls
from p2p_server import ListableNode

WIN_WIDTH = 512
WIN_HEIGHT = 300
ICON_APP = './icon/apple.png'

class GuiClient(QtGui.QWidget):
	"""
	a simple client with gui
	"""
	def __init__(self,port,dirname,ipsfile):
		# start node server first
		self.initNodeService(port,dirname,ipsfile)
		# init gui
		super(GuiClient,self).__init__()
		self.initUI()
	
	def initNodeService(self,port,dirname,ipsfile):
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

	def initUI(self):
		btn = QtGui.QPushButton('Fetch',self)
		btn.resize(btn.sizeHint())
	
		# settings for window
		self.resize(WIN_WIDTH,WIN_HEIGHT)
		#self.move(200,200)
		self.center()
		self.setWindowTitle('File Sharing Client')
		self.setWindowIcon(QtGui.QIcon(ICON_APP))
		self.show()

	def center(self):
		mbr = self.frameGeometry()
        	cen = QtGui.QDesktopWidget().availableGeometry().center()
        	mbr.moveCenter(cen)
        	self.move(mbr.topLeft())
	
	def closeEvent(self,event):
		# If we close the QtGui.QWidget, the QtGui.QCloseEvent is generated and closeEvent is called.
        	reply = QtGui.QMessageBox.question(self, 'Message', "Are you sure to quit?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes) 
        	if reply == QtGui.QMessageBox.Yes:
			# when exit,inform other nodes 
			self.do_exit()
            		event.accept()
       		else:
            		event.ignore()        

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

def main():
	app = QtGui.QApplication(sys.argv)
	client = GuiClient(PORT,SHARED_FOLDER,IPS_FILE)
	sys.exit(app.exec_())

if __name__ =='__main__':
	main()
