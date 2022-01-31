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

class TrackChannels:

	def __init__(self, markerId):
		self.markerId = markerId
		
		self.listenToChannel = {}
		self.listenToChannel[1] = False
		self.listenToChannel[2] = False
		self.listenToChannel[3] = False
		self.listenToChannel[4] = False

		self.channelMessages = {}
		self.channelMessages[1] = []
		self.channelMessages[2] = []
		self.channelMessages[3] = []
		self.channelMessages[4] = []

		self.recievedMarkers = []
