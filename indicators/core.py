#!/usr/bin/env python3

## @package indicators.core
#  The core for indicators module.
#
#  Provides basic Period, Time Series, and Ticker functionality.
#  Also provides helper functions for interacting with AlphaVantage.

import datetime
import json
import urllib.request
import configparser

config = configparser.ConfigParser(interpolation=None)
config.read('config.ini')
APIOpts = config['API']
testingOpts = config['TESTING']

TEST_MODE = testingOpts.getboolean('TEST_MODE')

API_KEY = APIOpts['API_KEY']
endpoint_base = APIOpts['ENDPOINT_BASE']
endpoint_intraday = endpoint_base + APIOpts['ENDPOINT_INTRADAY_BASE'] + API_KEY

key_timeSeries = "Time Series (%dmin)"

def getData(endpoint):
	with urllib.request.urlopen(endpoint) as req:
		return json.loads(req.read())

def getPriceTimeSeries(ticker, interval):
	intervalMins = int(interval.total_seconds()/60)

	if (TEST_MODE):
		f = open(testingOpts['TEST_DATA'], "r")
		data = json.loads(f.read())
	else:
		data = getData(endpoint_intraday % (ticker, intervalMins))

	timeSeriesList = data[key_timeSeries % (intervalMins)]
	periods = {}
	for timestampString, periodStrings in timeSeriesList.items():
		timestamp = datetime.datetime.strptime(timestampString, "%Y-%m-%d %H:%M:%S")
		_open   = float(periodStrings["1. open"  ])
		_high   = float(periodStrings["2. high"  ])
		_low    = float(periodStrings["3. low"   ])
		_close  = float(periodStrings["4. close" ])
		_volume = float(periodStrings["5. volume"])
		period = PricePeriod(timestamp, _open, _high, _low, _close, _volume)
		periods[timestamp] = period

	return PriceTimeSeries(ticker, interval, periods)

class Period(object):
	def __init__(self, timestamp):
		self.timestamp = timestamp

class TimeSeries(object):
	def __init__(self, ticker, interval, periods = None):
		periods = {} if periods == None else periods

		self.ticker = ticker
		self.interval = interval #timeDelta
		self.periods = periods
		self.timestampIndecies = []

		self.update()

	def __iter__(self):
		self.iterIndex = -1
		return self

	def __next__(self):
		self.iterIndex += 1
		if self.iterIndex < len(self.timestampIndecies):
			return self[self.iterIndex]
		else:
			raise StopIteration

	def __getitem__(self, key):
		if isinstance(key, datetime.datetime):
			return self.periods[key]
		elif isinstance(key, slice):
			return [self[i] for i in range(key.start if isinstance(key.start, int) else 0, 
										   key.stop if isinstance(key.stop, int)   else len(self.timestampIndecies),
										   key.step if isinstance(key.step, int)   else 1)]
		elif isinstance(key, int):
			return self.periods[self.timestampIndecies[key]]

	def __setitem__(self, key, value):
		if isinstance(key, datetime.datetime):
			self.periods[key] = value
		elif isinstance(key, int):
			if (self.timestampIndecies[key].timestamp != value.timestamp):
				raise ValueError("The period being replaced must have the same timestamp as its key")
			else:
				self.periods[self.timestampIndecies[key]] = value

	def __contains__(self, timestamp):
		return timestamp in self.timestampIndecies

	def __len__(self):
		return len(self.timestampIndecies)

	def __repr__(self):
		periodStrs = [str(p) for ts, p in self.periods.items()]
		return '\n'.join(periodStrs)

	def latest(self):
		return self.periods[max(self.timestampIndecies)]

	def earliest(self):
		return self.periods[min(self.timestampIndecies)]

	def updateWithTimeSeries(self, timeSeries):
		for p in timeSeries:
			if p.timestamp not in self:
				self.periods[p.timestamp] = p

		self.update()

	def update(self):
		self.timestampIndecies = sorted(self.periods.keys())

class PricePeriod(Period):
	def __init__(self, timestamp, _open, _high, _low, _close, _volume):
		super().__init__(timestamp)

		self.open = _open
		self.high = _high
		self.low = _low
		self.close = _close
		self.volume = _volume

	def __repr__(self):
		return "%s:\nopen:%f\nhigh:%f\nlow:%f\nclose:%f\nvolume:%f" % (self.timestamp.strftime("%Y-%m-%d %H:%M:%S"), self.open, self.high, self.low, self.close, self.volume)

class PriceTimeSeries(TimeSeries):
	def __init__(self, ticker, interval, periods = None):
		periods = {} if periods == None else periods
		
		super().__init__(ticker, interval, periods)

class Ticker(object):
	def __init__(self, ticker, interval = datetime.timedelta(minutes=15)):
		self.ticker = ticker
		self.timeSeries = PriceTimeSeries(ticker, interval)
		self.updateTimeSeries()

	def updateTimeSeries(self):
		newTimeSeries = getPriceTimeSeries(self.ticker, self.timeSeries.interval)
		self.timeSeries.updateWithTimeSeries(newTimeSeries)