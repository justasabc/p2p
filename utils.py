import os
from os.path import join,abspath
import socket
import urllib2
import re
from urlparse import urlparse
from random import choice
from string import lowercase
# by kzl
from settings import URL_PREFIX,PORT

# get local and external ip addres of this computer
# gethostname gethostb_ex only apply on windows

# method1: on windows and linux
if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

# method2: on windows and linux
def get_lan_ip2():
	try:
		s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		s.connect(('baidu.com', 80))
		ip = s.getsockname()[0]
		s.close()
		return ip
	except Exception, e:
		print e
		return ""

"""
"http://www.canyouseeme.org/"
"http://www.whatsmyip.org"
"http://www.whatsmyip.net"
"http://whatismyipaddress.com",
"http://www.whatismyip.org/"
"""

def get_wan_ip():
	p = "(\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3})"
	s = "http://www.canyouseeme.org/"
	try:
		html = urllib2.urlopen(s).read()	
		#html ="<td>Your IP:</td><td><b>162.105.17.48</b></td>"		
		m = re.search(p,html)
		if m:
			ip = m.group(0)
			return ip
	except Exception, e:
		print e
		return ""
	

def inside(dirname,filepath):
	"""
         check whether file exists in dir folder 
	 ./share/  ./share/11.txt
        """
	absdir = abspath(dirname)
	absfile = abspath(filepath)
	# make sure absdir2 end with '/'
	absdir2 = join(absdir,'')
	return absfile.startswith(absdir2)

def getport(url):
        """
        get port number from url like http://localhost:5555
        """
        name = urlparse(url)[1] # localhost:5555
        parts = name.split(':')
	return int(parts[-1])

def randomstring(length):
         """
         generate a random string for given length
         """
         chars = []
         letters = lowercase[:26]
         while length>0:
                 length -=1
                 chars.append(choice(letters))
         return ''.join(chars)

def generate_urls(ipsfile):
        """
        generate urls from ips
        192.168.1.200--->http://192.168.1.200:11111
        """
        for line in open(ipsfile):
                ip = line.strip()
		if ip:
                	url = "{0}{1}:{2}".format(URL_PREFIX,ip,PORT)
                	yield url

def main():
	print get_lan_ip()
	print get_lan_ip2()
	print get_wan_ip()
	print getport('http://localhost:5555')
	print randomstring(100)
	for url in generate_urls('ips.txt'):
		print url

	dirname = './share/'
	filepath = './share/11.txt'
	print inside(dirname,filepath)

	dirname = './share/'
	filepath = './11.txt'
	print inside(dirname,filepath)

if __name__ =='__main__':
	main()
