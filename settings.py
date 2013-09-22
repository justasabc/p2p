import logging
import SimpleXMLRPCServer

# settings for server and client

#logger
logging.basicConfig(level = logging.DEBUG)
#logging.basicConfig(filename='p2p.log',level = logging.DEBUG)
#logging.basicConfig(filename='p2p.log',level=logging.DEBUG,format='%(lev        elname)s %(asctime)s %(message)s')
mylogger = logging.getLogger('xxx')

# settings
SimpleXMLRPCServer.allow_reuse_address = 1
MAX_HISTORY_LENGTH = 6

NOT_EXIST = -1
ACCESS_DENIED = 0
SUCCESS = 1

# settings for ip and port
# http://192.168.1.200:12345
URL_PREFIX = "http://"
PORT=31111 
SHARED_FOLDER = "./share/"

# settings for client
SERVER_START_TIME = 0.1
SECRET_LENGTH = 100 
IPS_FILE= "./ips.txt"
