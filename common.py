class Messages:
	def __init__(self, reqType, fromClient, markerId = "", amount = 0):	
		self.reqType = reqType
		self.fromClient = fromClient
		self.markerId = markerId
		self.amount = amount

class State:
	def __init__(self, reqType, localState, channelState):
		self.reqType = reqType
		self.localState = localState
		self.channelState = channelState

