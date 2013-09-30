import logging
import SimpleXMLRPCServer

# settings for server and client

#logger
logging.basicConfig(level = logging.DEBUG)
#logging.basicConfig(filename='default.log',level = logging.DEBUG)
#logging.basicConfig(filename='p2p.log',level=logging.DEBUG,format='%(lev        elname)s %(asctime)s %(message)s')
mylogger = logging.getLogger('KZL')

SimpleXMLRPCServer.allow_reuse_address = 1
MAX_HISTORY_LENGTH = 6

NOT_EXIST = -1
ACCESS_DENIED = 0
ALREADY_EXIST = 1
SUCCESS = 2

# settings for ip and port
# http://192.168.1.200:12345
URL_PREFIX = "http://"
PORT=11111 
SHARED_FOLDER = "./share/"

# settings for client
SERVER_START_TIME = 0.1
SECRET_LENGTH = 100 
IPS_FILE= "./ips.txt"

# setting for file
CHUNK_SIZE = 1024*64

# settings for GUI
WIN_WIDTH = 1024
WIN_HEIGHT = 600
ICON_FLODER = './icon/'
ICON_APP = ICON_FLODER+'apple.png'
ICON_FETCH = ICON_FLODER+'fetch.png'
ICON_QUIT = ICON_FLODER+'quit.png'
UPDATE_INTERVAL = 3.0 # every n seconds upodate gui list
