#!/usr/bin/env python3

import indicators
import json
import urllib.request
import time

import indicators.core
import indicators.macd


def crossOver(message):
	print(message)

MTEM = indicators.core.Ticker("AAPL")
MACD = indicators.macd.MACDTimeSeries.MACDFromPriceTimeSeries(MTEM.timeSeries)
MACD.subscribe(crossOver)

while input("Press any key to reload data, or q to quit.") != "q":
	MTEM.updateTimeSeries()
	MACD.updateWithTimeSeries(MTEM.timeSeries)