from xmlrpclib import ServerProxy,Fault
import socket
import sys

port = 12345
if len(sys.argv)>=2:
	port = int(sys.argv[1])

ip = 'localhost'
url = 'http://{0}:{1}'.format(ip,port)
s = ServerProxy(url,allow_none=True)
try:
	print(s.twice(2)) # Call a fictive method.
	data = s.hello()
	print('data from hello')
	print(data)
	#print(s.xxx()) # not exist
except Fault:
        # connected to the server and the method doesn't exist which is expected.
	print('Connected to server but the method does not exist')
        pass
except socket.error:
        # Not connected ; socket error mean that the service is unreachable.
	print('Can not connect to server')

