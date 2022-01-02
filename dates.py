#!/usr/bin/python

import sys
import datetime

MONTH_ABBR = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
MONTH_LONG = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']

class Date:
	def __init__(self):
		d = datetime.date.today()
		self.year  = d.year
		self.month = d.month
		self.day   = d.day
		self.format = 'YYYY-MM-DD'
	
	def set_date(self, year, month, day):
		if year < 20:
			year = 2000 + year
		elif year < 100:
			year = 1900 + year
		self.year  = year
		self.month = month
		self.day   = day
	
	def __cmp__(self, other):
		if other == None: return 1
		if self.year  != other.year:  return self.year  - other.year
		if self.month != other.month: return self.month - other.month
		if self.day   != other.day:   return self.day   - other.day
		return 0
	def __lt__(self, other):
		return self.__cmp__(other) < 0
	def __gt__(self, other):
		return self.__cmp__(other) > 0
	def __eq__(self, other):
		return self.__cmp__(other) == 0
	
	def __str__(self):
		result = self.format
		
		result = result.replace('YYYY', '%s' % self.year)
		result = result.replace('YY',   '%02d' % (self.year % 100))
		result = result.replace('Y',    '%d' % (self.year % 100))
		
		result = result.replace('DD', '%02d' % self.day)
		result = result.replace('D',  '%d'  % self.day)
		
		if 'MMMM' in result:
			result = result.replace('MMMM', MONTH_LONG[self.month-1].upper())
		elif 'mmmm' in result:
			result = result.replace('mmmm', MONTH_LONG[self.month-1].lower())
		elif 'MMM' in result:
			result = result.replace('MMM',  MONTH_ABBR[self.month-1].upper())
		elif 'mmm' in result:
			result = result.replace('mmm',  MONTH_ABBR[self.month-1].lower())
		elif 'MM' in result:
			result = result.replace('MM',   '%02d' % self.month)
		elif 'M' in result:
			result = result.replace('M',    '%d'  % self.month)
		
		return result
	
	def set_format(self, format):
		if format != None:
			self.format = format
	
	# Increment to next valid date
	def next(self):
		self.day += 1
		reset = False
		if self.month == 2:
			# February (ugh)
			if self.day == 29:
				#if self.year % 4 == 0 and (not self.year % 100 == 0 or self.year % 400 == 0):
				if self.year % 4 != 0 or (self.year % 100 == 0 and self.year % 400 != 0):
					reset = True
			if self.day > 29:
				reset = True
			
		elif self.month in [1, 3, 5, 7, 8, 10, 12]:
			# 31 days
			if self.day > 31:
				reset = True
		elif self.day > 30:
			# 30 days
			reset = True
		
		if reset:
			self.day = 1
			self.month += 1

		if self.month > 12:
			self.month = 1
			self.year += 1
			if self.year < 1000 and self.year > 99:
				self.year = 0

def usage():
	print ('''
/ dates generator /

usage:
  ./dates.py <START_DATE> [END_DATE] [FORMAT]

date input:
  YYYY-MM-DD
	
formats:
  D \t day as single digit if applicable
  DD \t day as double digits always (leading zero)
  
  M \t month as single digit if applicable
  MM \t month as double digits always (leading zero)
	mmm \t month text abbreviation (jan, feb, mar)
	MMM \t month text abbreviation (JAN, FEB, MAR)
	mmmm \t month text lower-case (january, february)
	MMMM \t month text upper-case (JANUARY, FEBRUARY)
  
  Y \t year as single digit if applicable
  YY \t year as double digits always
  YYYY \t four-digit year

defaults:
  END_DATE \t current date (today)
  FORMAT \t YYYY-MM-DD

examples:
  # To print all dates since Jan 1, 1970:
  ./dates.py 1970-1-1 DDMMYYYY
  
	# To dump the dates to an 'output' file:
	./dates.py 1970-1-1 2000-1-1 > output.txt
''')

""" Retrieves start date, end date, and format to output """
def parse_input():
	args = sys.argv[1:]
	format = None
	if len(args) == 0:
		usage()
		sys.exit(1)
	elif len(args) == 1:
		start = args[0]
		stop   = str(datetime.date.today())
	elif len(args) == 2:
		start  = args[0]
		if not 'M' in args[1] and not 'm' in args[1] and not 'D' in args[1] and not 'd' in args[1] and not 'Y' in args[1] and not 'y' in args[1]:
			stop = args[1]
		else:
			stop   = str(datetime.date.today())
			format = args[1]
	elif not 'M' in args[1] and not 'm' in args[1] and not 'D' in args[1] and not 'd' in args[1] and not 'Y' in args[1] and not 'y' in args[1]:
		start  = args[0]
		stop   = args[1]
		format = ' '.join(args[2:])
	else:
		start = args[0]
		stop = str(datetime.date.today())
		format = ' '.join(args[1:])
	return (start, stop, format)

""" Retrieves year, month, and day (ints) from text """
def parse_date(text):
	if len(text) < 6: return None
	if '/' in text: text = text.replace('/', '-')
	if not '-' in text: 
		if len(text) == 8:
			text = text[:4] + '-' + text[4:6] + '-' + text[6:]
		else: return None
	if text.count('-') != 2: return None
	(syear, smonth, sday) = text.split('-')
	if smonth.lower() in MONTH_ABBR: smonth = MONTH_ABBR.index(smonth.lower()) + 1
	try:
		year = int(syear); month = int(smonth); day = int(sday)
	except ValueError: return None
	d = Date()
	d.set_date(year, month, day)
	return d

""" MAGIC """
def main():
	(start, stop, format) = parse_input()
	start_date = parse_date(start)
	stop_date  = parse_date(stop)
	if start_date == None or stop_date == None:
		print ('  unexpected year input(s): %s and %s' % (start, stop))
		print ('  use format:  YYYY-MM-DD')
		print ('  for example: 1970-01-01')
		sys.exit(1)
	start_date.set_format(format)
	print (start_date)
	while (start_date < stop_date):
		start_date.next()
		print (start_date)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print ('\n(^C) interrupted')
