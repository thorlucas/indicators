from .core import *
from .ema import *

# TODO: Do we even need this?

class MACDPeriod(Period):
	def __init__(self, timestamp, MACD, signal):
		super().__init__(timestamp)
		self.MACD = MACD
		self.signal = signal
		self.histogram = MACD - signal

	def __repr__(self):
		return "MACD at %s: %f, signal: %f, histogram: %f" % (self.timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.MACD, self.signal, self.histogram)

class MACDTimeSeries(TimeSeries):
	def __init__(self, ticker, interval, periods = {}):
		super().__init__(ticker, interval, periods)

		self.EMA26 = EMATimeSeries(ticker, interval, 26)
		self.EMA12 = EMATimeSeries(ticker, interval, 12)
		self.MACDEMA = None # Calculated from EMA12-EMA26
		self.signalEMA = EMATimeSeries(ticker, interval, 9, key = lambda p: p.EMA)
		self.histogram = None # Calculated from MACD - Signal

		self.subscriberCallback = None
		self.subscriberLastIndex = 1
		self.subscriberLastSign = None

	@classmethod
	def MACDFromPriceTimeSeries(cls, timeSeries):
		MACD = cls(timeSeries.ticker, timeSeries.interval)
		MACD.updateWithTimeSeries(timeSeries)

		return MACD

	def __getitem__(self, key):
		if isinstance(key, datetime.datetime):
			return MACDPeriod(key, self.MACDEMA[key].EMA, self.signalEMA[key].EMA)
		elif isinstance(key, slice):
			return [self[i] for i in range(key.start if isinstance(key.start, int) else 0, 
										   key.stop if isinstance(key.stop, int)   else len(self.histogram),
										   key.step if isinstance(key.step, int)   else 1)]
		elif isinstance(key, int):
			ts = self.histogram[key].timestamp
			return MACDPeriod(ts, self.MACDEMA[ts].EMA, self.signalEMA[ts].EMA)

	def updateWithTimeSeries(self, timeSeries):
		self.EMA12.updateWithTimeSeries(timeSeries)
		self.EMA26.updateWithTimeSeries(timeSeries)
		
		self.MACDEMA = self.EMA12 - self.EMA26
		self.signalEMA.updateWithTimeSeries(self.MACDEMA)

		self.histogram = self.MACDEMA - self.signalEMA
		self.checkSubscriptions()

	def subscribe(self, callback):
		self.subscriberCallback = callback
		self.checkSubscriptions()

	def checkSubscriptions(self):
		if (self.subscriberCallback == None): return

		if (self.subscriberLastSign == None):
			self.subscriberLastSign = self[0].histogram / abs(self[0].histogram)

		for p in self[self.subscriberLastIndex:]:
			if p.histogram / abs(p.histogram) != self.subscriberLastSign:
				self.subscriberLastSign *= -1
				self.subscriberCallback(Notification(p.timestamp, "MACD", self.subscriberLastSign))

			self.subscriberLastIndex += 1