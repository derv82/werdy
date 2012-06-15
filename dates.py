#!/usr/bin/python

import sys
import datetime

MONTH_ABBR = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

def usage():
	print '''
/ dates generator /

usage:
  ./dates.py <START_DATE> [END_DATE] <FORMAT>

date input:
  YYYY-MM-DD
	
formats:
  D \t day as single digit if applicable
  DD \t day as double digits always (leading zero)
  
  M \t month as single digit if applicable
  MM \t month as double digits always (leading zero)
  
  Y \t year as single digit if applicable
  YY \t year as double digits always
  YYYY \t four-digit year

examples:
	./dates.py 1970-1-1 2000-12-21 DDMMYYYY
'''

""" Retrieves start date, end date, and format to output """
def parse_input():
	args = sys.argv[1:]
	if len(args) < 2:
		usage()
		sys.exit(1)
	elif len(args) == 2:
		start  = args[0]
		stop   = str(datetime.date.today())
		format = args[1]
	else:
		start  = args[0]
		stop   = args[1]
		format = ' '.join(args[2:])
	return (start, stop, format)

""" Retrieves year, month, and day (ints) from text """
def parse_date(text):
	if len(text) < 6: return (None, None, None)
	if '/' in text: text = text.replace('/', '-')
	if not '-' in text: 
		if len(text) == 8:
			text = text[:4] + '-' + text[4:6] + '-' + text[6:]
		else: return (None, None, None)
	if text.count('-') != 2: return (None, None, None)
	(syear, smonth, sday) = text.split('-')
	if smonth.lower() in MONTH_ABBR: smonth = MONTH_ABBR.index(smonth.lower()) + 1
	try:
		year = int(syear); month = int(smonth); day = int(sday)
	except ValueError: return (None, None, None)
	return (year, month, day)

""" MAGIC """
def main():
	(start, stop, format) = parse_input()
	(ystart, mstart, dstart) = parse_date(start)
	(ystop,  mstop,  dstop)  = parse_date(stop)
	if ystart == None or ystop == None:
		print '  unexpected year input(s): %s and %s' % (start, stop)
		print '  use format:  YYYY-MM-DD'
		print '  for example: 1970-01-01'
		sys.exit(1)
	print 'start: %d-%d-%d ... stop: %d-%d-%d' % (ystart, mstart, dstart, ystop, mstop, dstop)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print '\n(^C) interrupted'
