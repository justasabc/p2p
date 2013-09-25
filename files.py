import sys
import os
import xmlrpclib
# by kzl
from settings import CHUNK_SIZE

rootdir = './share/'

def list_all_files_test(rootdir):
	for root,subFolders,files in os.walk(rootdir):
		print("rootdir: {0}".format(root)) 
		for filename in files:
			filepath = os.path.join(root,filename)
			print filepath
		for folder in subFolders:
			print("subfolder: {0}".format(folder))

def list_all_files(rootdir):
	"""
	list all flies in rootdir recursively
	return filepath list
	"""
	allfiles = []
	for root,subFolders,files in os.walk(rootdir):
		for filename in files:
			filepath = os.path.join(root,filename)
			allfiles.append(filepath)
	return allfiles

def list_all_files_generator(rootdir):
	"""
	list all flies in rootdir recursively
	return a generator
	"""
	for root,subFolders,files in os.walk(rootdir):
		for filename in files:
			filepath = os.path.join(root,filename)
			yield filepath

def savefile_frombinary(filepath,data):
	with open(filepath,'wb') as f:
		f.write(data)

def savefile_frombinary_xmlrpc(filepath,data):
	with open(filepath,'wb') as f:
		f.write(data.data)

def savefile_fromtext(filepath,data):
	with open(filepath,'w') as f:
		f.write(data)

def readfile_asbinary(filepath):
	with open(filepath,'rb') as f:
		return f.read()

def readfile_asbinary_xmlrpc(filepath):
	with open(filepath,'rb') as f:
		return xmlrpclib.Binary(f.read())

def readfile_astext(filepath):
	with open(filepath,'r') as f:
		return f.read()

count = 0
def read_in_chunks2(filepath,chunksize=CHUNK_SIZE):
	global count
	with open(filepath,'rb') as f:
		while True:
			print 'reading...'
			chunk = f.read(chunksize)
			if not chunk:
				break
			for b in chunk:
				count = count +1
				yield b

def read_in_chunks(filepath,chunksize=CHUNK_SIZE):
	with open(filepath,'rb') as f:
		while True:
			chunk = f.read(chunksize)
			if chunk:
				yield chunk
			else:
				return

def savefile(filepath,newfilepath):
	with open(newfilepath,'wb') as f:
		for chunk in read_in_chunks(filepath):
			f.write(chunk)
def main():
	for f in list_all_files(rootdir):
		print f

	filepath = './share/image/IMG_0004.JPG'
	newfilepath = '1.JPG'
	data = readfile_asbinary(filepath)
	savefile_frombinary(newfilepath,data)
	"""
	filepath = './share/image/IMG_2749.JPG'
	newfilepath = '1.JPG'
	savefile(filepath,newfilepath)
	"""
if __name__ =="__main__":
	main()
