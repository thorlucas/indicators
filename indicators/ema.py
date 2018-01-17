#!/usr/bin/env python3

from .core import *
from .notification import *

class EMAPeriod(Period):
	def __init__(self, timestamp, EMA):
		super().__init__(timestamp)

		self.EMA = EMA

	def __repr__(self):
		return "%s: %f" % (self.timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.EMA)

	def __add_(self, other):
		return EMAPeriod(self.timestamp, self.EMA + other.EMA)

	def __sub__(self, other):
		return EMAPeriod(self.timestamp, self.EMA - other.EMA)

class EMATimeSeries(TimeSeries):
	def __init__(self, ticker, interval, EMALength = None, periods = None, key = lambda p: p.close):
		periods = {} if periods == None else periods
		super().__init__(ticker, interval, periods)

		self.EMALength = EMALength
		self.key = key

		self.subscriberCallback = None
		self.subscriberThreshold = None
		self.subscriberLastIndex = 1
		self.subscriberLastSign = None

	@classmethod
	def EMAFromPriceTimeSeries(cls, timeSeries, EMALength):
		EMA = cls(timeSeries.ticker, timeSeries.interval, EMALength)
		EMA.updateWithTimeSeries(timeSeries)

		return EMA

	def __add__(self, other):
		lesserEMA = self if len(self) < len(other) else other
		newPeriods = {}
		for ts in lesserEMA.timestampIndecies:
			newEMAPeriod = self[ts] + other[ts]
			newPeriods[newEMAPeriod.timestamp] = newEMAPeriod

		return EMATimeSeries(self.ticker, self.interval, periods = newPeriods)

	def __sub__(self, other):
		lesserEMA = self if len(self) < len(other) else other
		newPeriods = {}
		for ts in lesserEMA.timestampIndecies:
			newEMAPeriod = self[ts] - other[ts]
			newPeriods[newEMAPeriod.timestamp] = newEMAPeriod

		return EMATimeSeries(self.ticker, self.interval, periods = newPeriods)

	def __repr__(self):
		periodStrs = ["EMA(%d) for %s:" % (self.EMALength if isinstance(self.EMALength, int) else -1, self.ticker)] + [str(p) for ts, p in self.periods.items()]
		return '\n'.join(periodStrs)

	def subscribe(self, threshold, callback):
		self.subscriberThreshold = threshold
		self.subscriberCallback = callback
		self.checkSubscriptions()

	def updateWithTimeSeries(self, timeSeries):
		if not self.timestampIndecies:
			initEMAValue = sum([self.key(p) for p in timeSeries[0:self.EMALength]]) / self.EMALength
			initEMATimestamp = timeSeries[self.EMALength - 1].timestamp
			initEMA = EMAPeriod(initEMATimestamp, initEMAValue)
			self[initEMATimestamp] = initEMA
			self.timestampIndecies = [initEMATimestamp]

			EMAIndexStart = self.EMALength
		else:
			EMAIndexStart = timeSeries.timestampIndecies.index(self.timestampIndecies[-1]) + 1

		# TODO: catch for index errors etc.

		multiplier = 2.0 / (self.EMALength + 1)

		for pricePeriod in timeSeries[EMAIndexStart:]:
			priceTimestamp = pricePeriod.timestamp
			prevEMA = self[-1]
			EMAValue = (self.key(pricePeriod) - prevEMA.EMA) * multiplier + prevEMA.EMA
			EMA = EMAPeriod(priceTimestamp, EMAValue)
			self[priceTimestamp] = EMA
			self.timestampIndecies.append(priceTimestamp)

		# # TODO: Might not need this since everything should be in order
		self.update()
		self.checkSubscriptions()

	def checkSubscriptions(self):
		if (self.subscriberCallback == None): return

		if (self.subscriberLastSign == None):
			self.subscriberLastSign = (self[0].EMA - self.subscriberThreshold)/abs(self[0].EMA - self.subscriberThreshold)

		for p in self[self.subscriberLastIndex:]:
			if (p.EMA - self.subscriberThreshold)/abs(p.EMA - self.subscriberThreshold) != self.subscriberLastSign:
				self.subscriberLastSign *= -1
				self.subscriberCallback(Notification(p.timestamp, "EMA", self.subscriberLastSign))
				
			self.subscriberLastIndex += 1



