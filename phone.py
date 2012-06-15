#!/usr/bin/python
import os, httplib, sys, time

"""

This script generates lists of phone numbers given a city or area code within the U.S.

For more information, type:
python phone.py ?

(C) 2011 Derv Merkler

"""

# separators
sep1 = ''
sep2 = ''
sep3 = '-'

area = ''
city = ''

file = 'phone.txt'

no_area = False

STATES = []
STATES.append(("ALABAMA ", "AL"))
STATES.append(("ALASKA ", "AK"))
STATES.append(("AMERICAN SAMOA ", "AS"))
STATES.append(("ARIZONA ", "AZ"))
STATES.append(("ARKANSAS ", "AR"))
STATES.append(("CALIFORNIA ", "CA"))
STATES.append(("COLORADO ", "CO"))
STATES.append(("CONNECTICUT ", "CT"))
STATES.append(("DELAWARE ", "DE"))
STATES.append(("DISTRICT OF COLUMBIA ", "DC"))
STATES.append(("FEDERATED STATES OF MICRONESIA ", "FM"))
STATES.append(("FLORIDA ", "FL"))
STATES.append(("GEORGIA ", "GA"))
STATES.append(("GUAM GU ", "GU"))
STATES.append(("HAWAII ", "HI"))
STATES.append(("IDAHO ", "ID"))
STATES.append(("ILLINOIS ", "IL"))
STATES.append(("INDIANA ", "IN"))
STATES.append(("IOWA ", "IA"))
STATES.append(("KANSAS ", "KS"))
STATES.append(("KENTUCKY ", "KY"))
STATES.append(("LOUISIANA ", "LA"))
STATES.append(("MAINE ", "ME"))
STATES.append(("MARSHALL ISLANDS ", "MH"))
STATES.append(("MARYLAND ", "MD"))
STATES.append(("MASSACHUSETTS ", "MA"))
STATES.append(("MICHIGAN ", "MI"))
STATES.append(("MINNESOTA ", "MN"))
STATES.append(("MISSISSIPPI ", "MS"))
STATES.append(("MISSOURI ", "MO"))
STATES.append(("MONTANA ", "MT"))
STATES.append(("NEBRASKA ", "NE"))
STATES.append(("NEVADA ", "NV"))
STATES.append(("NEW HAMPSHIRE ", "NH"))
STATES.append(("NEW JERSEY ", "NJ"))
STATES.append(("NEW MEXICO ", "NM"))
STATES.append(("NEW YORK ", "NY"))
STATES.append(("NORTH CAROLINA ", "NC"))
STATES.append(("NORTH DAKOTA ", "ND"))
STATES.append(("NORTHERN MARIANA ISLANDS ", "MP"))
STATES.append(("OHIO ", "OH"))
STATES.append(("OKLAHOMA ", "OK"))
STATES.append(("OREGON ", "OR"))
STATES.append(("PALAU ", "PW"))
STATES.append(("PENNSYLVANIA ", "PA"))
STATES.append(("PUERTO RICO ", "PR"))
STATES.append(("RHODE ISLAND ", "RI"))
STATES.append(("SOUTH CAROLINA ", "SC"))
STATES.append(("SOUTH DAKOTA ", "SD"))
STATES.append(("TENNESSEE ", "TN"))
STATES.append(("TEXAS ", "TX"))
STATES.append(("UTAH ", "UT"))
STATES.append(("VERMONT ", "VT"))
STATES.append(("VIRGIN ISLANDS ", "VI"))
STATES.append(("VIRGINIA ", "VA"))
STATES.append(("WASHINGTON ", "WA"))
STATES.append(("WEST VIRGINIA ", "WV"))
STATES.append(("WISCONSIN ", "WI"))
STATES.append(("WYOMING ", "WY"))


# Looks through a source string for all items between two other strings, 
# returns the list of items (or empty list if none are found)
def between(source, start, finish):
  result = []
  
  i = source.find(start)
  j = source.find(finish, i + len(start) + 1)
  
  while i >= 0 and j >= 0:
    i = i + len(start)
    
    result.append(source[i:j])
    
    i = source.find(start, i + len(start) + 1)
    j = source.find(finish, i + len(start) + 1)
  
  return result

# returns page source for given url
def getweb(url):
  if url.startswith('http://'):
    url = url[len('http://'):]
  if url.startswith('https://'):
    url = url[len('https://'):]
  
  
  if url.find('/') == -1:
    domain = url
    path = '/'
  else:
    domain = url[0:url.find('/')]
    path   = url[len(domain):]
  
  try_again = True
  while try_again:
    try_again = False
    try:
      h = httplib.HTTP(domain)
      h.putrequest('GET', path)
      h.putheader('Host', domain)
      h.putheader('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30')
      h.endheaders()
      returncode, returnmsg, headers = h.getreply()
    except Exception, e:
      print '\nError! "' + str(e).strip() + '" waiting 10 seconds',
      try_again = True
      time.sleep(10)
    
  return h.getfile().read()

# returns list (strings) of area codes and prefixes for given city
# format is areacode-prefix, with a dash separating them.
def prefixes_city(city):
  r = getweb('http://www.melissadata.com/lookups/phonelocation.asp?number=' + city)
  result = []
  for num in between(r, '0000">', '</a'):
    num = num.replace('-', '')
    
    if no_area:
      result.append(num[3:6] + sep3)
    else:
      result.append(sep1 + num[0:3] + sep2 + num[3:6] + sep3)
  return result

# returns list (strings) of area codes and prefixes for a given area code
# format is areacode-prefix
def prefixes_areacode(code):
  r = getweb('http://www.melissadata.com/lookups/phonelocation.asp?number=' + str(code))
  result = []
  cities = between(r, "<a href='phonelocation.asp?number=", "'>")
  for city in cities:
    city = city.replace('&state=', ',')
    result.extend(prefixes_city(city))
    
  return result

def help():
  h = """
  this script generates lists of phone numbers within the U.S.
  
  usage: python phone.py [OPTIONS]
  
  OPTIONS:
    
    ?         this help screen
    
    -area     the 3-digit area code to grab phone numbers from
    
    -city     the city combination to grab phone numbers from
              include a comma and the state abbr for more specificity
              ex: -city albuquerque,nm
              ex: -city new+york,ny
    
    -------------------------------------------------------------------
    
    -sep1 $   sets first separator to $   default is blank
              ex: -sep1 ( would result in phone numbers that resemble:
                  (555256-0101
    -sep2 $   sets second separator to $  default is blank
              ex: -sep2 ) would result in phone numbers that resemble:
                  555)256-0101
    -sep3 $   sets third separator to $   default is -
              ex: -sep3 x would result in phone numbers that resemble:
                  555256x0101
    
    to include spaces in the separators...
          * windows: use quotes, as in -sep3 " "
          * unix:    use backslash, as in -sep3 \  
    
    -noarea   ignore area code.           result: 2560101
              area code and first two separators will not be printed.
    
    -nosep    no separators are printed.  result: 5552560101
    
  """
  print h


def autopwn():
  """
    Automatically look up user's location based on their IP address,
    Then find city/state format via USPS.com
  """
  r = getweb('http://whatismyipaddress.com/')
  c = between(r, '<tr><th>City:</th><td>', '</td></tr>')
  s = between(r, '<tr><th>Region:</th><td>', '</td></tr>')
  if len(c) == 0 or len(s) == 0:
    return ''

  if 'Region:' in c[0] or 'Country:' in s[0]: return ''

  state = ''
  for st in STATES:
    # print st[0].replace('\t', '').strip()
    print state
    if s[0].upper() == st[0].replace('\t', '').strip():
      state = st[1]
      break
  
  return c[0].replace(' ', '+') + "+" + state


def parse_args(args):
  """
    Parses command-line arguments. Sets global variables, etc.
  """
  global sep1, sep2, sep3, no_area, area, city, file
  
  i = 0
  while i < len(args):
    if args[i] == '?' or args[i] == '/?' or args[i] == '-h' or args[i] == '-help' or args[i] == '--help' or args[i] == '-?':
      help()
      sys.exit(0)
      
    if args[i] == '-sep1':
      sep1 = args[i+1]
      i += 1
    elif args[i] == '-sep2':
      sep2 = args[i+1]
      i += 1
    elif args[i] == '-sep3':
      sep3 = args[i+1]
      i += 1
    
    elif args[i] == '-noarea':
      no_area = True
      file = 'noarea-' + file
      
    elif args[i] == '-nosep':
      sep1, sep2, sep3 = '', '', ''
      file = 'nosep-' + file
    
    elif args[i] == '-area':
      area = args[i+1]
      if not area.isdigit() or len(area) != 3:
        print '\n * area code must be 3 digits long!'
        sys.exit(0)
      i += 1
    elif args[i] == '-city':
      city = args[i+1]
      i += 1
      
    elif args[i] == '-o':
      file = args[i+1]
      i += 1
      
    elif city != '':
      city += '+' + args[i]
    
    i += 1


def main(args):
  """
    Where the magic happens.
  """
  global file, city
  
  print '\n / phone number list magic /'
  
  parse_args(args)
  
  print ''
  
  if area == '' and city == '':
    print ' * CITY or AREA CODE required!'
    print ' attempting to lookup city,state based on your ip address...',
    sys.stdout.flush()
    city = autopwn()
    if city == '':
      print 'unsuccessful!'
      print ' to input a city, type -city ALBUQUERQUE'
      print ' to input an area code, type -area 505'
      print '\n type python phone.py -h for more detailed instructions'
      sys.exit(0)
    print 'found "' + city + '"'
    file = city + '-' + file
    
  elif area != '':
    file = area + '-' + file
  elif city != '':
    file = city + '-' + file
  
  if os.path.exists(file) and os.path.isfile(file):
    print ' * the file "' + file + '" already exists!'
    print ' do you want to overwrite this file? (Y/N)',
    
    input = raw_input().lower()
    if input == '': input = 'n'
    if input[0] != 'y':
      print ' * exiting'
      sys.exit(0)
    os.remove(file)
  
  before = time.time()
  
  if area != '':
    print ' searching for phone numbers with area code "' + area + '"...'
    lst = prefixes_areacode(area)
    
  elif city != '':
    print ' searching for phone numbers within city "' + city + '"...'
    lst = prefixes_city(city)
  
  print ''
  
  if len(lst) == 0:
    print ' * no phone number prefixes found!'
    print ' ensure city/areacode is correct and that they are within the U.S.'
    sys.exit(0)
  
  print ' %s prefixes found. %s total phone numbers possible' % (format(len(lst), ',d'), format(10000 * len(lst), ',d'))
  print ''
  
  total = 0
  f = open(file, 'wb')
  for prefix in lst:
    for i in xrange(0, 10000):
      f.write('%s%04d\n' % (prefix, i))
    print '\r generated phone numbers for prefix %s' % (prefix),
    total += 1
  
  f.close()
  
  print '\n\n total phone numbers: %s, saved to %s' % (format(10000 * total, ',d'), file)
  print ' finished in %.2fs' % (time.time() - before)


if __name__ == '__main__':
  """
    Only run when executed.
  """
  try:
    main(sys.argv[1:])
  except KeyboardInterrupt:
    print '\n\n^C Interrupted'
  
