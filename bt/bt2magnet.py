import sys
from os.path import isfile
import libtorrent as bt

print(sys.argv)
if len(sys.argv)<2:
	print('Please enter bt file')
	sys.exit()
filepath = sys.argv[1]
if not filepath.endswith('.torrent'):
	print('File is not torrent')
	sys.exit()
if not isfile(filepath):
	print('File does not exist')
	sys.exit()

info = bt.torrent_info(filepath)
strbt = "magnet:?xt=urn:btih:{0}&dn={1}".format(info.info_hash().upper(), info.name())
