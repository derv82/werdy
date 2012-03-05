#!/usr/bin/python

import sys, os, time

"""

todo: placeholders : @@@asdf@@@ creates 000asdf000, 000asdf001, etc...
       ^ i like crunch's use of ^#$@
      stop at word
      break into lines


You can pipe the output of this script into aircrack-ng...

python crunch.py -lower -m 8 | aircrack-ng.exe -a 2 -w - -e "<ROUTER ESSID>" <CAP_FILE>.cap      

"""

length_min = 0
length_max = 0

charset    = ''

output     = '-'

ch_alpha_u = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ch_alpha_l = 'abcdefghijklmnopqrstuvwxyz'
ch_numbers = '0123456789'
ch_symbol1 = '!@#$%^&*()_+-=,.'
ch_symbol2 = """`~[]\{}|;':"/<>?"""

mask       = ''

bytes_max  = 0
lines_max  = 0

lines_total= 0

resume_string = ''

# prints to stderr
def p(txt):
  sys.stderr.write(txt)

# generate the next file
# uses syntax of file.txt -> file-1.txt -> file-2.txt -> etc
def next_file(file):
  s = file.rfind(os.sep)
  c = file.rfind('.', s + 1)
  if c == -1: c = len(file)
  
  if file[:c].find('-') == -1:
    return file[:c] + '-1' + file[c:]
  else:
    d = file[:c].rfind('-')
    
    try:
      temp = int(file[d+1:c])
    except ValueError:
      return file[:c] + '-1' + file[c:]
    return file[:d] + '-' + str(temp + 1) + '' + file[c:]
  

# starts the generator
def gen():
  global resume_string, output
  
  # check if output file already exists.
  
  if output != '-' and os.path.exists(output):
    
    # enumerate *all* files, if they exist
    to_remove = []
    while os.path.exists(output):
      to_remove.append(output)
      output = next_file(output)
      
    output = to_remove[-1]
    file   = open(output, 'r')
    file.seek(-128, os.SEEK_END)
    chunk  = file.read(128)
    file.close()
    
    chunks = chunk.split('\n')
    last_line = chunks[len(chunks) - 2]
    
    p('\n the file %s already exists.\n')
    p(' the last line of %s is "%s"\n\n' % (output, last_line))
    
    p(' type f to resume [f]rom %s' % last_line)
    if resume_string != '':
      p('\n      r to [r]esume from %s' % resume_string)
    p('\n   or d to [d]elete %s and start from the beginning: ' % output)
    
    answer = raw_input().lower()
    if len(answer) < 1:
      p('\n invalid input, exiting\n\n')
      sys.exit(0)
      
    elif answer[0] == 'r':
      p('\n resuming from %s\n\n' % resume_string)
      
    elif answer[0] == 'd':
      p('\n deleting %s and starting from beginning.\n\n' % (output))
      for f in to_remove:
        os.remove(f)
      output = to_remove[0]
      resume_string = ''
      
    else:
      resume_string = last_line
      p('\n resuming from %s\n' % resume_string)
      
  
  if mask != '':
    gen_mask()
    
  else:
    
    the_min = length_min
    if resume_string != '':
      the_min = len(resume_string)
      if length_min > the_min or length_max < the_min:
        p('\n invalid resume length: %d\n\n' % the_min)
        the_min = length_min
        resume_string = ''
    
    for length in xrange(the_min, length_max + 1):
      gen_len(length)
      resume_string = ''

def gen_mask():
  global lines_total, output, resume_string
  
  time_before = time.time()
  
  bytes_cur = 0
  if os.path.exists(output):
    bytes_cur = os.path.getsize(output)
  
  if output == '-':
    outfile = sys.stdout
  else:
    outfile = open(output, 'a')
  
  length = len(mask.replace('\\',''))
  
  i = 0
  escape_char = False
  lst = [0] * length
  chlst = [[0]] * length
  for letter in mask:
    chlst[i] = []
    
    if escape_char:
      chlst[i].append(letter)
      escape_char = False
    elif letter == '@': # lower alpha
      for c in ch_alpha_l:
        chlst[i].append(c)
    elif letter == ',': # upper alpha
      for c in ch_alpha_u:
        chlst[i].append(c)
    elif letter == '$': # symbols
      for c in (ch_symbol1 + ch_symbol2):
        chlst[i].append(c)
    elif letter == '%': # numbers
      for x in xrange(0, 10):
        chlst[i].append(str(x))
    elif letter == '\\':
      escape_char = True
      continue
    else:
      chlst[i].append(letter)
    i += 1
    
  if resume_string != '':
    for i, letter in enumerate(resume_string):
      lst[i] = None
      for j, x in enumerate(chlst[i]):
        if x == letter:
          lst[i] = j
          break
      if lst[i] == None:
        # unable to find letter, default to nothing
        lst = [0] * len(mask)
        break
  
  lines_max = 1
  for x in xrange(0, length):
    lines_max *= (len(chlst[x]))
  
  i = length - 1
  print_it = True
  
  while i >= 0:
    if print_it:
      if output != '-' and lines_total % 35000 == 0:
        p('\r "')
        for x, y in enumerate(lst):
          p(chlst[x][y])
        p('"   %.2f%%' % (100 * float(lines_total) / lines_max))
        if lines_total != 0:
          p(' ETA: %s       ' % sectotime((time.time() - time_before) / lines_total * (lines_max - lines_total)))
      
      if bytes_max > 0 and output != '-' and bytes_cur + length + 1 >= bytes_max:
        outfile.close()
        output = next_file(output)
        bytes_cur = 0
        if os.path.exists(output): bytes_cur = os.path.getsize(output)
        outfile = open(output, 'a')
        
      for x, y in enumerate(lst):
        outfile.write(chlst[x][y])
        if bytes_max > 0: bytes_cur += 1
      outfile.write('\n')
      bytes_cur += 2
      lines_total += 1
      print_it = False
    
    lst[i] += 1
    if lst[i] >= len(chlst[i]):
      lst[i] = 0
      i -= 1
    else:
      i = length - 1
      print_it = True
    
  if output != '-':
    p('\r word length: %d, wrote %s lines (%s) to %s\n' % (length, format(lines_total, ',d'), inttosize(os.path.getsize(output)), output))
    outfile.close()


# writes words of len 'length' to 'outfile'
# resumes from 'resume_string', if it's possible
def gen_len(length):
  global lines_total, output, resume_string
  
  time_before = time.time()
  
  if output == '-':
    outfile = sys.stdout
  else:
    bytes_cur = 0
    if os.path.exists(output): bytes_cur = os.path.getsize(output)
    outfile = open(output, 'a')
  
  lst = [0] * length
  if len(resume_string) == length and resume_string != '':
    for i, letter in enumerate(resume_string):
      if charset.find(letter) == -1:
        p('\n invalid resume string: "%s"\n\n' % resume_string)
        lst = [0] * length
        break
      lst[i] = charset.find(letter)
  
  lines_max = 1
  for l in lst:
    lines_max *= (len(charset) - l)
  
  i = length - 1
  print_it = True
  
  while i >= 0:
    if print_it:
      if output != '-' and lines_total % 35000 == 0:
        p('\r (%d)   "' % (length))
        for j in lst:
          p(charset[j])
        p('"   %.2f%%' % (100 * float(lines_total) / lines_max))
        if lines_total != 0:
          p(' ETA: %s       ' % sectotime((time.time() - time_before) / lines_total * (lines_max - lines_total)))
      
      if bytes_max > 0 and output != '-' and bytes_cur + length + 2 >= bytes_max:
        outfile.close()
        output = next_file(output)
        bytes_cur = 0
        if os.path.exists(output): bytes_cur = os.path.getsize(output)
        outfile = open(output, 'a')
      
      for j in lst:
        outfile.write(charset[j])
        if output != '-': bytes_cur += 1
      outfile.write('\n')
      if output != '-': bytes_cur += 2
      
      lines_total += 1
      print_it = False
    
    lst[i] += 1
    if lst[i] >= len(charset):
      lst[i] = 0
      i -= 1
    else:
      i = length - 1
      print_it = True
    
  if output != '-':
    p('\r word length: %d, wrote %s lines (%s) to %s\n' % (length, format(lines_total, ',d'), inttosize(os.path.getsize(output)), output))
    outfile.close()


# converts numeric bytes into human-readable format
def inttosize(bytes):
  b = 1024 * 1024 * 1024 * 1024
  a = ['t','g','m','k','']
  for i in a:
    if bytes >= b:
      return '%.2f%sb' % (float(bytes) / float(b), i)
    b /= 1024
  return '0b'

# converts string representation of a filesize to int (bytse)
# ex: sizetoint('1mb') returns 1048576
def sizetoint(size):
  snum = ''
  for char in size:
    if char.isdigit() or char == '.': 
      snum += char
    else:
      break
  num = float(snum)
  
  chars = size[len(snum):].strip().lower()
  chars = chars.replace('b','')
  if chars == 't':
    num = num * 1024 * 1024 * 1024 * 1024
  elif chars == 'g':
    num = num * 1024 * 1024 * 1024
  elif chars == 'm':
    num = num * 1024 * 1024
  elif chars == 'k':
    num = num * 1024
  
  return int(num)

# converts seconds to human-readable format
# ex: sectotime(3661) returns '1h 1m 1.00s'
def sectotime(sec):
  result = ''
  
  if sec > 3600:
    result = '%dh ' % (sec / 3600)
  
  sec %= 3600
  if sec > 60:
    result += '%dm ' % (sec / 60)
  
  sec %= 60
  if result == '':
    result = str('%.2fs' % sec)
  else:
    result += str('%ds' % sec)
    
  return result

# print the hlp screen
def help():
  p("""
 USAGE: python crunch.py -m <min> -M <max> [OPTIONS]

 OPTIONS:
  
  -o FILE      specify output file. generated words will be saved to FILE
               ex: -o -              will print to stdout (default)
               ex: -o wordlist.txt   will save words to the file wordlist.txt
  
  -min MIN     set minimum word length to MIN (number)
  -max MAX     set maximum word length to MAX (number)
  
  -lower, -l   add lower-case letters (a-z) to the character set
  -upper, -u   add upper-case letters (A-Z) to the character set
  -nums,  -n   add numbers (0-9) to the character set
  -sym1        add common symbols !@#$%^&*()_+-=,. to the character set
  -sym2        add uncommon symbols `~[]\{}|;':"/<>? to the character set
  -symbols     add both common and uncommon symbols to the char set
  
  -c SET       add a custom set of charaters (SET) to the character set
               ex: -c rstlne12345
  
  -resume WORD resumes wordlist generation from WORD.
               ex: "-m 3 -l -resume mmm" would generate mmm, mmn, mmo, mmp...
  
  -mask MASK   generates permutations around the given MASK
                 @ inserts lower-case alphabet letters (a-z)
                 , inserts upper-case alphabet letters (A-Z)
                 % inserts numbers (0-9)
                 $ inserts symbols
  
  -b BYTES     specify the maximum file size. 
               output files will not exceed size BYTES
               BYTES can be written in # of bytes (ie 1048576) 
               or in human-readable (ie 10mb) ex: -b 1gb
  """)

# parse the command-line arguments, set global variables
def parse(args):
  global charset, length_min, length_max, output, bytes_max, resume_string, mask
  
  i = 0
  while i < len(args):
    # charsets
    if args[i] == '-lower' or args[i] == '-l':
      charset += ch_alpha_l
    elif args[i] == '-upper' or args[i] == '-u':
      charset += ch_alpha_u
    elif args[i] == '-n' or args[i] == '-num' or args[i] == '-nums' or args[i] == '-numbers':
      charset += ch_numbers
      
    elif args[i] == '-sym1' or args[i] == '-symbol1':
      charset += ch_symbol1
    elif args[i] == '-sym2' or args[i] == '-symbol2':
      charset += ch_symbol2
    elif args[i] == '-symbols':
      charset += ch_symbol1 + ch_symbol2
      
    elif args[i] == '-char' or args[i] == '-chars' or args[i] == '--chars' or args[i] == '--char' or args[i] == '-c':
      charset += args[i+1]
      i += 1
      
    # length
    elif args[i] == '-m' or args[i] == '-min' or args[i] == '--min':
      length_min = int(args[i+1])
      if length_max == 0: length_max = length_min
      p(' minimum word length: %d\n' % length_min)
      i += 1
      
    elif args[i] == '-M' or args[i] == '--max' or args[i] == '-max' or args[i] == '-MAX':
      length_max = int(args[i+1])
      if length_min == 0: length_min = length_max
      p(' maximum word length: %d\n' % length_max)
      i += 1
    
    # output
    elif args[i] == '-o' or args[i] == '-output' or args[i] == '--output':
      output = args[i+1]
      p(' list will be saved to "' + output + '"\n')
      i += 1
    
    # bytes
    elif args[i] == '-b' or args[i] == '-bytes' or args[i] == '--bytes':
      bytes_max = sizetoint(args[i+1])
      i += 1
    
    # resume
    elif args[i] == '-r' or args[i] == '-resume' or args[i] == '--resume' or args[i] == '--r' or args[i] == '-res' or args[i] == '--res':
      resume_string = args[i+1]
      i += 1
      
    # mask
    elif args[i] == '-mask' or args[i] == '--mask':
      mask = args[i+1]
      i += 1
      
    # help
    elif args[i] == '?' or args[i] == '/?' or args[i] == '-help' or args[i] == '--help' or args[i] == 'help':
      help()
      sys.exit(0)
    i += 1
  
  if len(args) == 0:
    help()
    exit(1)

  if length_min == 0:
    if mask == '':
      p('\n no minimum/maximum length given!')
      p('\n use -m or -M to set min/max word length\n exiting\n')
      sys.exit(0)
    else:
      p('\n using word mask: "%s"\n' % mask)
    
  # default to use lower-case alphabet character set
  if charset == '':
    charset = ch_alpha_l
    
  else:
    # check for and remove duplicates in the character set
    for c in charset:
      count = charset.count(c)
      if count > 1:
        charset = charset.replace(c, '', count - 1)
  
  if bytes_max != 0:
    p(' maximum file size: %s bytes\n' % format(bytes_max, ',d'))
  p('\n using character set:\n    %s\n\n' % charset)

# main!
if __name__ == '__main__':
  try:
    p('\n / wordlist generator magic /\n')
    parse(sys.argv[1:])
    gen()
  except KeyboardInterrupt:
    p('\n\n ^C Interrupted')
  except IOError:
    p('\n\n IOError received, exiting\n\n')
    sys.exit(0)
