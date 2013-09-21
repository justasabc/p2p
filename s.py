from SimpleXMLRPCServer import SimpleXMLRPCServer
SimpleXMLRPCServer.allow_reuse_address = 1
t = ('',12345)
s = SimpleXMLRPCServer(t,allow_none=True)
def twice(x):
	return x*2
def hello():
	return None
s.register_function(twice)
s.register_function(hello)
print('Server is running...')
s.serve_forever()
