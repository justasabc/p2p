import os
import socket
import urllib2
import re

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
	


def main():
	print get_lan_ip()
	print get_lan_ip2()
	print get_wan_ip()

if __name__ =='__main__':
	main()
