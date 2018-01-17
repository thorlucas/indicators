import datetime

class Notification():
	def __init__(self, timestamp, name, sign):
		self.timestamp = timestamp
		self.name = name
		self.sign = sign

	def __repr__(self):
		return "%s %s crossover at %s" % (self.name, "Negative" if self.sign < 0 else "Positive", self.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
