from scipy.signal import convolve
def convolve(x, h):
	y = convolve(x, h)
	return y

class convolveNode(lg.Node):
	INPUT = lg.Topic(InputMessage)
	OUTPUT = lg.Topic(OutputMessage)

	def setup(self):
		self.func = convolve

	@lg.subscriber(INPUT)
	@lg.publisher(OUTPUT)

	def convolve_feature(self, message: InputMessage):
		y = self.func(message.x, message.h)
		yield self.OUTPUT, y