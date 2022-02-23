#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

"""
(C) Derv Merkler 2011

What this script does:
  1) reads from 1 or many text files
  2) sorts all lines in the file
  3) removes duplicates (if any are found)
  4) saves the sorted/dupe-killed lines to a new file


// DONE:

 * "file kill" option to delete input files after they are read.
     results in only 1X extra file space used instead of 2X.
     
 * warning about making disk space available for output file *AND* chunks
    ex: sorting 2GB word of wordlists requires 4GB free space.
    
 * "convert case" option to possible option to "save as lowercase/upper/FirstLetter"
    this would save items in the list as lowercase rather than saving the item AND saving the lower-case equivalent.

 * allow creation of similar words (lcase, UCASE, First)
    duplicates will most likely be created.
    the disk space used could multiply for each case type used
    ex: using lcase and ucase may cause the disk space used to be 3x original file size.

 * convert_case is now working (lower upper first leetify)
    
// TODO:
 
 * dragging-dropping files makes CWD = C:\Windows\system32.. which is bad
    we don't want to save sort.txt to system32... 
 
 * alter 'freq sort' so that when the max chunk size is reached,
    it removes all elements of frequency freq_min or less, and increments freq_min += 1
 
 * create copy of leetify text
 
 * specify that '-w' only removes whitespace characters AT THE BEGINNING/END of the line!!
    update help() to show this.
    
 * stats on # of non-printing characters removed.
 
 * add support for mac-formatted EOL files 
    (probably not gonna happen - .readline() does not work well w/ mac files)
 
"""

import sys            # for command-line arguments
import os             # for file-system purposes
import time           # for calculating running time
import heapq          # for merging text files
import tempfile       # for creating temporary directory
import math           # calculating logarithms
import platform       # for identifying operating system
import ctypes         # for grabbing disk free space (Windows)
from glob import glob # for grabbing files from directory via wildcards


# stripping non-printing characters
import unicodedata, re
control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
control_char_re = re.compile('[%s]' % re.escape(control_chars))

strip_nonprinting = True # default to stripping the characters
# this is slightly slower but definitely useful and likely to be used for password lists

strip_whitespace = True # remove leading/trailing whitespace characters of each line

outfile = 'sort.txt'  # file to save to (changable via -o switch)

length_min   = 0      # -m
length_max   = 0      # -M

remove_dupes = True   # -d

# size to split the output file into (output files will not exceed this number of bytes)
split_size   = 1024 * 1024 * 1024 * 10 # 10GB

# size to split input files into (use a smaller number for less RAM usage)
chunk_size   = 1024 * 1024 * 500       # 500MB

update_every = 50000    # every ___ words to update percentages

left_sep      = ''      # left separator
right_sep     = ''      # right separator

delete_string = []      # lines containing these strings will be skipped

# number of words removed and why
words_removed_short = 0
words_removed_long  = 0
words_removed_dupe  = 0
words_removed_blank = 0
words_removed_del   = 0

rjust = 28 # column length for file names. used for right-justification
njust = 13 # column length for word totals.

convert_case = '' # case to convert to, lcase, ucase, first

# make-a-copy flags for different cases
copy_lower = False
copy_upper = False
copy_first = False
copy_leetify = False

delete_input = False # delete the input file(s) after data is parsed.

# temporary directory
temp_dir = tempfile.mkdtemp(prefix='sort')
if not temp_dir.endswith(os.sep): temp_dir += os.sep

# frequency variables
freq_flag       = False  # sort list by how frequently the lines appeared (most frequent first)
freq_show_count = False  # display the number of times a word appeared
freq_min        = 0      # minimum times a word must appear to be counted as 'frequent'

# input: a word, a case (lcase, upper, first, etc)
# output: the word, in the given case.
# ex: convert("oh hi", 'first') returns "Oh hi"
def convert(word, case):
  if case == 'lcase' or case == 'lower':
    return word.lower()
  elif case == 'ucase' or case == 'upper' or len(word) <= 1 and case == 'first':
    return word.upper()
  elif case == 'first':
    return word[0].upper() + word[1:].lower()
  elif case == 'leetify':
    for leet in leetify(word):
      return leet
    
  return word

# generator for leet speak text
def leetify(text):
  leet=[['a','4','@'],
        ['b','8'],
        ['c','('],
        ['d'],
        ['e','3'],
        ['f'],
        ['g','9'],
        ['h','#'],
        ['i','1','!'],
        ['l','7','1'], # '!',
        ['m','nn'],
        ['o','0'], # '()',
        ['s','5','$'], # ,'z'
        ['t','7','+'],
        ['w'], # ,'vv'
        ['z','2']]
  
  list  = [0] * len(text)
  count = [0] * len(text)
  for i, letter in enumerate(text):
    letter = letter.lower()
    found = False
    for l in leet:
      if letter == l[0]:
        found = True
        list[i] = l
        count[i] = min(1, len(list[i]) - 1)
        break
    if not found:
      list[i]  = [letter]
      count[i] = 0
  count[len(text) - 1] = 0
  
  ind = len(count) - 1
  while ind >= 0:
    count[ind] += 1
    if count[ind] >= len(list[ind]):
      count[ind] = min(1, len(list[ind]) - 1)
      ind -= 1
    else:
      ind = len(text) - 1
      s = ''
      for x in xrange(0, len(list)):
        s += list[x][count[x]]
      yield s


# first half of the sorting process
# input: list of files
# output: list of filenames containing all data from input files,
#         each file is sorted in non-decreasing order, 
#         each file is at most of size chunk_size, and has all invalid lines removed.
def split(files):
  global length_min, length_max, split_size, remove_dupes, update_every
  global words_removed_short, words_removed_long, words_removed_blank, words_removed_del
  global left_sep, right_sep, delete_string, strip_whitespace, convert_case
  global copy_lower, copy_upper, copy_first, copy_leetify, strip_nonprinting
  
  split_file = 0  # current chunk filename we are creating
  bytes_cur  = 0  # current amount of bytes in this chunk (not to exceed chunk_size)
  lst        = [] # contains lines of current chunk
  
  words_total, words_kept, files_loaded= 0, 0, 0 # counters
  
  still_sorted = True
  for file in files: # iterate over every file in input
    
    if not os.path.exists(file):
      print '\n file not found: "' + file + '"',
      sys.stdout.flush()
      continue
    elif not os.path.isfile(file):
      print '\n skipping directory: "' + file + '"',
      sys.stdout.flush()
      continue
    
    print ''
    files_loaded += 1
    
    words_in_file, words_created = 0, 0
    file_cur, file_len = 0, os.path.getsize(file) # current/total bytes in this file
    
    last = ''
    
    i = open(file, 'rb')
    line = i.readline()
    while line:
      if words_total % update_every == 0: # only print out every so often so we are no encumbered by std out
        print '\r loading%s, words: %s (%.2f%%)  ' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust), (100 * float(file_cur) / float(file_len))),
        sys.stdout.flush()
      
      words_in_file += 1
      
      file_cur += len(line) # update current location in this file
      
      if strip_nonprinting: # check for non-printing stripping
        line = control_char_re.sub('', line)
      
      if strip_whitespace:  # check for white-space stripping
        line = line.strip()
      elif line.endswith('\n') != -1:
        line = line.replace('\n', '')
      
      save = True  # flag, tells us if line should be saved
      
      # check for left-separator option
      if left_sep != '': 
        if line.rfind(left_sep) == -1:
          save = False
        else:
          line = line[:line.rfind(left_sep)]
        
      # check for right-separator option
      if right_sep != '':
        if line.find(right_sep) == -1:
          save = False
        else:
          line = line[line.find(right_sep) + len(right_sep):]
      
      # check for delete-string option
      for de in delete_string:
        if line.find(de) != -1:
          save = False
          words_removed_del += 1
          break
      
      # check for blank-line
      if len(line) == 0:
        save = False
        words_total -= 1
        words_removed_blank += 1
      
      # minimum length option
      elif length_min > 0 and len(line.replace('\n','')) < length_min:
        save = False
        words_removed_short += 1
      
      # maximum length option
      elif length_max > 0 and len(line.replace('\n','')) > length_max:
        save = False
        words_removed_long += 1
      
      
      if save: # if we are still supposed to save it, do it
        bytes_cur += len(line) + 1



        #check if we have to convert case
        if convert_case:
          converted_line = convert(line, convert_case)
          lst.append(converted_line)
        else:
          lst.append(line)
        words_kept += 1
        
        if still_sorted and cmp(last, line) > 0:
          still_sorted = False
        
        # make copies in diff cases (if needed)
        if copy_lower and line.lower() != line:
          if still_sorted: still_sorted = False
          lst.append(line.lower())
          bytes_cur += len(line) + 1
          words_created += 1
      
        if copy_upper and line.upper() != line:
          if still_sorted: still_sorted = False
          lst.append(line.upper())
          bytes_cur += len(line) + 1
          words_created += 1
      
        if copy_first:
          temp = convert(line, 'first')
          if temp != line:
            if still_sorted: still_sorted = False
            lst.append(temp)
            bytes_cur += len(temp) + 1
            words_created += 1
      
        if copy_leetify:
          if still_sorted: still_sorted = False
          for leetify_perm in leetify(line):
            if words_created % update_every == 0:
              print '\r loading%s, words: %s (%.2f%%)  ' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust), (100 * float(file_cur) / float(file_len))),
              sys.stdout.flush()
            lst.append(leetify_perm)
            bytes_cur += len(leetify_perm) + 1
            words_created += 1
            if bytes_cur >= chunk_size: 
              print '\r loading%s, words: %s *sorting*' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
              sys.stdout.flush()
              
              lst.sort()         # sort the chunk
              still_sorted = True
              
              print '\r loading%s, words: %s *chunking*' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
              sys.stdout.flush()
              
              o = open(temp_dir + str(split_file), 'wb') 
              for item in lst: # save the chunk
                o.write(item + '\n')
              o.close()
              
              del lst[:]
              
              split_file += 1  # increment the current chunk file
              bytes_cur = 0
              
              print '\r loading%s, words: %s (%.2f%%)  ' % (filename(file).rjust(rjust), format(words_in_file, ',d').rjust(njust), (100 * float(file_cur) / float(file_len))),
              sys.stdout.flush()
      words_total += 1
      
      # check if we have exceeded the chunk size while iterating over this file
      if bytes_cur >= chunk_size: 
        print '\r loading%s, words: %s *sorting*' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
        sys.stdout.flush()
        
        if not still_sorted: # the list is not already sorted
          lst.sort()         # sort the chunk
        still_sorted = True
        
        print '\r loading%s, words: %s *chunking*' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
        sys.stdout.flush()
        
        o = open(temp_dir + str(split_file), 'wb') 
        for item in lst: # save the chunk
          o.write(item + '\n')
        o.close()
        
        del lst[:]
        
        split_file += 1  # increment the current chunk file
        bytes_cur = 0
        
        print '\r loading%s, words: %s           ' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
        sys.stdout.flush()
        
      last = line
      line = i.readline()
    
    i.close()
    print '\r loaded %s, words: %s           ' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
    sys.stdout.flush()
    
    if delete_input:
      os.remove(file)
      print '\r loaded %s, words: %s *deleted* ' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
      sys.stdout.flush()
  
  # at this point, we are done extracting data from the list of input files
  
  if files_loaded == 0:
    print '\n no files found! exiting'
    sys.exit(0)
    
  # check if there are still items left in the chunk to be saved
  if len(lst) > 0:
    print '\r loaded %s, words: %s *sorting*' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
    sys.stdout.flush()
    
    if not still_sorted: # the list is not already sorted
      lst.sort()         # sort the chunk
    
    print '\r loaded %s, words: %s *chunking*' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
    sys.stdout.flush()
    
    o = open(temp_dir + str(split_file), 'wb')
    o.write('\n'.join(lst)) # save the chunk
    o.close()
    
    del lst[:]
    split_file += 1
    print '\r loaded %s, words: %s            ' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
    sys.stdout.flush()
    
    if delete_input:
      #os.remove(file)
      print '\r loaded %s, words: %s *deleted* ' % (filename(file).rjust(rjust), format(words_in_file + words_created, ',d').rjust(njust)),
      sys.stdout.flush()
      
  print '\n        ' + ('%d files' % (files_loaded)).rjust(rjust) + ', total: %s words' % (format(words_kept + words_created, ',d')).rjust(njust)
  
  result = []
  for x in xrange(0, split_file):
    result.append(temp_dir + str(x))
  
  return result # return list of filenames containing the sorted chunks

# generator for lines in a file. used by the 'merge' function
def file_gen(file):
  f = open(file, 'rb')
  line = f.readline()
  while line:
    yield line
    line = f.readline()
    
  f.close()
  os.remove(file)

# merge sorted chunks into one file
# input: 'chunks': list of filenames; each file is sorted
#        'file'  : filename to save list to
# result: all data contained in 'chunks' is saved to 'file', maintaining sorted order
#         'file' size will not exceed split_size (bytes)
def merge(chunks, file):
  global update_every, words_removed_dupe
  
  outfile = open(file, 'wb')
  
  saving_to = file # current file we are writing to (subject to change as size exceeds split_size)
  
  bytes_so_far, bytes_cur, count, split_file = 0, 0, 0, 0 # counters for bytes/lines
  
  # total number of bytes for all input files (awesome one-liner!)
  bytes_ttl = sum(os.path.getsize(str(chunk)) for chunk in chunks)
  
  words_in_file, words_kept, last = 0, 0, '' # word counters
  
  # frequency counters
  freq_count, freq_list = 1, []
  
  # we get to use the beautiful heapq.merge() method.
  # it will take our input files and grab the next-smallest word from each file! it's amazing!
  for line in heapq.merge(*(file_gen(f) for f in chunks)):
    
    if count % update_every == 0:
      if freq_flag:
        print '\r counting words: %s (%.3f%%)' % (format(words_in_file, ',d').rjust(njust), 100 * float(bytes_cur) / float(bytes_ttl)),
        sys.stdout.flush()
      else:
        print '\r saving ' + filename(saving_to).rjust(rjust) + ', words: %s (%.3f%%)' % (format(words_in_file, ',d').rjust(njust), 100 * float(bytes_cur) / float(bytes_ttl)),
        sys.stdout.flush()
    
    bytes_cur += len(line)
    
    if bytes_so_far + len(line) >= split_size:
      outfile.close()
      print '\r saved  ' + filename(saving_to).rjust(rjust) + ', words: %s (%s)      ' % (format(words_in_file, ',d').rjust(njust), inttosize(bytes_so_far))
      split_file += 1
      c = file.rfind('.')
      if c == -1: c = len(file) - 1
      saving_to = file[:c] + '-' + str(split_file) + '' + file[c:]
      outfile = open(saving_to, 'wb')
      words_in_file = 0
      bytes_so_far = 0
    
    if not remove_dupes or line != last:
      
      if freq_flag:
        if freq_count >= freq_min:
          freq_list.append((freq_count, last))
        
        # ensure the sorted list is not too big
        if sys.getsizeof(freq_list) > chunk_size:
          freq_list.sort(reverse=True) # reverse sort
          while sys.getsizeof(freq_list) > chunk_size:
            freq_list.pop(len(freq_list) - 1) # remove least-frequently-occuring element.
        freq_count = 1
      else:
        outfile.write(line)
        bytes_so_far += len(line)
        
      last = line
      words_in_file += 1
      words_kept += 1
    
    elif freq_flag:
      freq_count += 1
      pass
      
    else:
      words_removed_dupe += 1
      
    count += 1
  
  # calculating frequency of words, sorting, saving, etc
  if freq_flag and len(freq_list) > 0:
    print '\r counting words: %s (%.3f%%)' % (format(words_in_file, ',d').rjust(njust), 100 * float(bytes_cur) / float(bytes_ttl)),
    print '\n frequency sort: *sorting*...',
    sys.stdout.flush()
    
    freq_list.sort(reverse=True)
    
    print '\r frequency sort: *saving* to %s...' % (file),
    
    outfile = open(file, 'wb')
    just = len(str(freq_list[0][0]))
    
    if freq_show_count:
      outfile.write('#'.rjust(just) + ' word\n')
      outfile.write('%s %s\n' % ('-' * just, '-'* len(freq_list[0][1])))
    
    bytes_so_far = 0
    for item in freq_list:
      if freq_show_count:
        bytes_so_far += len(str(item[0]).rjust(just) + ' ' + item[1])
        outfile.write(str(item[0]).rjust(just) + ' ' + item[1])
      else:
        bytes_so_far += len(item[1])
        outfile.write(item[1])
    
    outfile.close()
    
    print '\r frequency sort: saved to %s (%s)' % (file, inttosize(bytes_so_far))
    
  elif freq_flag:
    print '\n frequency sort: no lines occurred more than %s times' % (freq_min)
  
  else:
    print '\r saved  ' + filename(saving_to).rjust(rjust) + ', words: %s (%s)      ' % (format(words_in_file, ',d').rjust(njust), inttosize(bytes_so_far))
    
    print '\n total words saved: %s' % (format(words_kept, ',d'))
    outfile.close()
    
# extract the filename from a path
def filename(path):
  s = path.rfind(os.sep)
  if s == -1:
    result = path
  else:
    result = path[s+1:]
  
  if len(result) < rjust:
    return result
  mid = int(rjust / 2)
  return result[:mid-1] + '...' + result[2+len(result)-mid:]

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

# converts numeric bytes into human-readable format
def inttosize(bytes):
  b = 1024 * 1024 * 1024 * 1024
  a = ['t','g','m','k','']
  for i in a:
    if bytes >= b:
      return '%.2f%sb' % (float(bytes) / float(b), i)
    b /= 1024
  return '0b'

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
  result += str('%.2fs' % sec)
  
  return result

# print help screen
def help():
  print ' this script sorts [and can clean] wordlists.'
  print ''
  print ' usage: python sort.py [OPTIONS] [FILE(S)]'
  print ''
  print ' OPTIONS:'
  print "   -o $       output file sorted data is written to. default: sort.txt"
  print "   -m #       minimum line length. lines shorter than # will be removed"
  print "   -M #       maximum line length. lines longer than # will be removed"
  print ""
  print "   -d         do NOT remove duplicates. default: remove duplicate lines"
  print ""
  print "   -s $       split output file into segments of size $"
  print "              ex: -s 100mb splits output into 100 megabyte chunks"
  print "              ex: -s 0.9gb splits output into 0.9 gigabyte chunks"
  print "              works with prefixes: [b], kb, mb, gb, or tb. default:", inttosize(split_size)
  print ""
  print "   -c #       chunk size. this decides how much data is loaded into memory"
  print "              smaller is safer, but slower. default:", inttosize(chunk_size)
  print ""
  print "   -freq      sort the list based on how frequently the lines appear"
  print "              list will be ordered from most-frequent to least-frequent"
  print "   -freqn     same as -freq, but also display # of times each line appeared"
  print "              the output will resemble a table instead of a list of words"
  print ""
  print "   -l $       in each line, extract text to the left of  $"
  print "   -r $       in each line, extract text to the right of $"
  print "              note: if separator is not found, line is ignored (removed)"
  print ""
  print "   -x $       ignore (do not save) line if it contains $. (case sensitive)"
  print "              note: you can use -x multiple times if desired"
  print ""
  print "   -np        DON'T strip non-printing characters from each line"
  print "   -w         DON'T strip leading/trailing whitespace characters from each line"
  print ""
  print "   -kill      deletes all input files as they are parsed."
  print "              this is useful if you want to free disk space during the sort"
  print "              WARNING: this will PERMANENTLY DELETE ALL FILES you pass to it"
  print "              this option only requires 1X input size free space instead of 2X"
  print ""
  print "   -convert $ convert lines to $ case: lower, upper, first, leetify."
  print "              ex: to convert list to lower-case, type: -convert lower"
  print ""
  print "   -lower     save copies of each line as lower-case"
  print "   -upper     save a copy of each line as UPPER-CASE"
  print "   -first     save a copy of each line as First Letter Capitalized"
  print "   -leetify     save a copy of each line as leetify (31337)"
  print ""
  print " example: python sort.py -m 8 -M 63 *.txt"

# return amount of free space (in bytes) available on the drive
# cross-platform!
def get_free_space(folder):
  if platform.system() == 'Windows':
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
    return free_bytes.value
  else:
    oss = os.statvfs(folder)
    return oss.f_bfree * oss.f_bsize

# return path to this file (sort.py)
def get_script_path():
  p = os.path.realpath(__file__)
  p = p[:p.rfind(os.sep)+1]
  return p

# ensures there is enough space in the temp folder and cwd for the files
# exits with error message if there may not be enough space
def filesize_check(files):
  total = sum(os.path.getsize(file) for file in files)
  grand_total = total
  
  delete_multiplier = 2
  if delete_input:
    delete_multiplier = 1
  
  if copy_lower:
    grand_total += total
  if copy_upper:
    grand_total += total
  if copy_first:
    grand_total += total
  
  cdir = os.getcwd()
  if platform.system() == 'Windows':
    cdir = cdir[:cdir.find(os.sep)+1]
  cwd_free = get_free_space(cdir)
  
  tdir = temp_dir
  if platform.system() == 'Windows':
    tdir = tdir[:tdir.find(os.sep)+1]
  tmp_free = get_free_space(tdir)
  
  not_enough = False
  
  if cwd_free == tmp_free:
    # cwd and tmp are the same disk
    grand_total * delete_multiplier
    if cwd_free < (grand_total):
      not_enough = True
      print ' * not enough space on disk ' + cdir
      print '\n the program may require up to %s free space' % (inttosize(grand_total))
      print ' free space available on %s: %s' % (cdir, inttosize(cwd_free))
      
  else:
    
    # cwd and tmp are separate disks
    if tmp_free < grand_total:
      not_enough = True
      print ' * not enough space on disk: ' + tdir
      print ' the program may require up to %s free space' % (inttosize(grand_total))
      print ' free space available on ' + tdir + ': %s' % (inttosize(tmp_free))
      
    elif not delete_input and cwd_free < grand_total:
      not_enough = True
      print ' * not enough space on disk: ' + cdir
      print '\n the program may require up to %s free space' % (inttosize(grand_total))
      print ' free space available on ' + cdir   + ': %s' % (inttosize(cwd_free))
      
    elif delete_input and cwd_free < grand_total - total:
      not_enough = True
      print ' * not enough space on disk: ' + cdir
      print ' the program may require up to %s free space' % (inttosize(grand_total - total))
      print '\n free space available on ' + cdir   + ': %s' % (inttosize(cwd_free))
      
      
  if not_enough:
    sys.exit(0)

# checks if 'file' and permutations of 'file' already exist,
# prompts the user to delete them if they do, otherwise outputs nothing.
def output_check(file):
  exists = []
  if os.path.exists(file):
    exists.append(file)
  
  c = file.rfind('.')
  if c == -1: c = len(file) - 1
  i = 1
  while os.path.exists(file[:c] + '-' + str(i) + file[c:]):
    exists.append(file[:c] + '-' + str(i) + file[c:])
    i += 1
  
  if len(exists) > 0:
    if len(exists) == 1:
      print ' the following file already exists and may be overwritten:'
    else:
      print ' the following files already exist and may be overwritten:'
    for i, e in enumerate(exists):
      if i < 4 or i > len(exists) - 3:
        print '  * ' + e
      else:
        print '.',
    
    if len(exists) == 1:
      print ' do you want to delete this file? (Y/N):',
    else:
      print ' do you want to delete these files? (Y/N):',
    
    x = raw_input().strip().lower()
    
    if x == '' or x[0] != 'y':
      print ''
      print ' you can specify the output file with the -o switch'
      print '   ex: python sort.py -o new_file.txt *.txt'
      sys.exit(0)
    for e in exists:
      os.remove(e)

# ensure the user wants to delete every input file before generating the output file
def delete_check(files):
  if delete_input:
    print '\n ************ WARNING ***************'
    print ''
    
    if len(files) > 1:
      print ' you have chosen to delete input files after they have been read'
    else:
      print ' you have chosen to delete the input file after it has been read'
    
    print ' this will PERMANENTLY DELETE the following file(s):'
    for f in files:
      print '   * ' + f
    
    print ' are you sure that you want to do this? (Y/N)',
    x = raw_input().lower()
    if x != 'y':
      print '\n exiting. run without the -kill option to avoid this warning'
      sys.exit(0)
    
    print '\n no, seriously, are you sure? (Y/N)',
    x = raw_input().lower()
    if x != 'y':
      print '\n exiting. run without the -kill option to avoid this warning'
      sys.exit(0)

# parse command-line arguments, set global variables
def parse_args(args):
  global length_min, length_max, remove_dupes
  global split_size, chunk_size, outfile
  global left_sep, right_sep, delete_string, strip_whitespace
  global freq_flag, freq_show_count, delete_input
  global convert_case, copy_lower, copy_upper, copy_first, copy_leetify
  global strip_nonprinting
  
  result, i = [], 0
  
  printed = False
  
  while i < len(args):
    x = args[i]
    
    if x == '-m' or x == '-min' or x == '--min':
      if i == len(args) - 1:
        print ' minimum length required!'
        sys.exit(0)
      length_min = int(args[i+1])
      printed = True
      print ' * minimum word length set: ' + str(length_min)
      i += 1
      
    elif x == '-M' or x == '-max' or x == '--max':
      if i == len(args) - 1:
        print ' maximum length required!'
        sys.exit(0)
      length_max = int(args[i+1])
      printed = True
      print ' * maximum word length set: ' + str(length_max)
      i += 1
      
    elif x == '-o' or x == '--output':
      if i == len(args) - 1:
        print ' output file name required!'
        sys.exit(0)
      outfile = args[i+1]
      print ' * output file set: "' + outfile + '"'
      i += 1
      
    elif x == '-d' or x == '--duplicates':
      remove_dupes = False
      printed = True
      print ' * duplicate removal disabled'
      
    elif x == '-s' or x == '--split':
      if i == len(args) - 1:
        print ' split size (in bytes) required!'
        sys.exit(0)
      split_size = sizetoint(args[i+1])
      printed = True
      print ' * file split size set: ' + format(split_size, ',d') + ' bytes'
      i += 1
      
    elif x == '-c' or x == '--chunk':
      if i == len(args) - 1:
        print ' chunk size (in bytes) required!'
        sys.exit(0)
      chunk_size = sizetoint(args[i+1])
      printed = True
      print ' * chunk size set:', format(chunk_size, ',d'), 'bytes'
      i += 1
      
    elif x == '-l' or x == '--left':
      if i == len(args) - 1:
        print ' separating string is required!'
        sys.exit(0)
      left_sep = args[i+1]
      printed = True
      print ' * left-separator set:', left_sep
      i += 1
      
    elif x == '-r' or x == '--right':
      if i == len(args) - 1:
        print ' separating string is required!'
        sys.exit(0)
      right_sep = args[i+1]
      printed = True
      print ' * right-separator set:', right_sep
      i += 1
      
    elif x == '-x' or x == '--skip':
      if i == len(args) - 1:
        print ' deletion string is required!'
        sys.exit(0)
      delete_string.append(args[i+1])
      printed = True
      print ' * deletion string added:', args[i+1]
      i += 1
      
    elif x == '-help' or x == '/?' or x == '--help' or x == '-h' or x == '?':
      help()
      sys.exit(0)
      
    elif x == '-wpa' or x == '--wpa':
      length_min = 8
      length_max = 63
      remove_dupes = True
      print ' *** WPA-PSK MODE ***'
      print ' * minimum word length set: ' + str(length_min)
      print ' * maximum word length set: ' + str(length_max)
      print ' * duplicate removal enabled'
      printed = True
      
    elif x == '-w' or x == '--no-strip':
      strip_whitespace = False
      print ' * whitespace stripping disabled'
      printed = True
      
    elif x == '-np' or x == '--non-printing':
      strip_nonprinting = False
      print ' * non-printing character stripping disabled'
      printed = True
      
    elif x == '-freq' or x == '--freq':
      freq_flag = True
      freq_show_count = False
      print ' * sorting by frequency enabled'
      printed = True
      
    elif x == '-freqn' or x == '--freq-count':
      freq_flag = True
      freq_show_count = True
      print ' * sorting by frequency enabled, line frequency is included in output'
      printed = True
      
    elif x == '-kill' or x == '--delete-input-files':
      delete_input = True
      
    elif x =='-convert' or x == '--convert':
      if i == len(args) - 1:
        print ' convert string case required! ex: lower, upper, first'
        sys.exit(0)
      convert_case = args[i+1]
      printed = True
      print ' * convert case set: ', convert(args[i+1], args[i+1])
      i += 1
      
    elif x == '-lower' or x =='-lcase':
      copy_lower = True
      print ' * lower-case copies enabled'
      printed = True
      
    elif x == '-upper' or x =='-ucase':
      copy_upper = True
      print ' * upper-case copies enabled'
      printed = True
      
    elif x == '-first' or x =='--first':
      copy_first = True
      print ' * first-letter-upper copies enabled'
      printed = True
      
    elif x == '-leetify' or x == '--leetify':
      copy_leetify = True
      print ' * leetify (leetspeak) mutations enabled'
      printed = True
      
    else:
      if x.find('*') != -1:
        fixed = ''
        for letter in x:
          if letter == '[':
            fixed += '[[]'
          elif letter == ']':
            fixed += '[]]'
          else:
            fixed += letter
        x = fixed
        for item in glob(x):
          result.append(item)
          
      elif os.path.isfile(x):
        result.append(x)
        
      elif os.path.isdir(x):
        if not x.endswith(os.sep):
          x += os.sep
        for item in glob(x + '*'):
          result.append(item)
    i += 1
  
  if printed: print ''
  
  return result

# where the magic happens!
def start(args):
  global outfile, words_removed_short, words_removed_long, words_removed_blank, words_removed_dupe, words_removed_del, delete_string
  print ""
  print " / derv's wordlist magic /"
  print ""
  
  files = parse_args(args)
  if len(files) == 0:
    help()
    print '\n no input files given!'
    sys.exit(0)
  
  
  if os.getcwd().lower() == 'c:\\windows\\system32':
    temp = files[0]
    os.chdir(temp[:temp.rfind(os.sep)+1])
    print ' * file(s) will be saved to "' + os.getcwd() + '"\n'
  
  delete_check(files)
  
  output_check(outfile)
  
  filesize_check(files)
  
  before = time.time()
  chunks = split(files)
  print ''
  merge(chunks, outfile)
  print '\n finished in %s' % (sectotime(time.time() - before))
  
  if words_removed_short > 0 or words_removed_long > 0 or words_removed_dupe > 0 or words_removed_blank > 0 or words_removed_del:
    print '\n removal statistics:'
    times = 0
    
    if words_removed_blank > 0:
      print '   * blanks:    %s words' % (format(words_removed_blank, ',d').rjust(njust))
      times += 1
    if words_removed_short > 0:
      print '   * too short: %s words' % (format(words_removed_short, ',d').rjust(njust))
      times += 1
      
    if words_removed_long > 0:
      print '   * too long:  %s words' % (format(words_removed_long,  ',d').rjust(njust))
      times += 1
      
    if words_removed_dupe > 0:
      print '   * duplicates:%s words' % (format(words_removed_dupe,  ',d').rjust(njust))
      times += 1
      
    if words_removed_del > 0:
      print '   * deleted:   %s words (contained %s)' % (format(words_removed_del,   ',d').rjust(njust), ' or '.join(delete_string))
      times += 1
      
    if times > 1:
      print '                 ------------------'
      print '   * total rm\'d:%s words' % (format(words_removed_blank+words_removed_dupe+words_removed_short+words_removed_long+words_removed_del, ',d').rjust(njust))

if __name__ == '__main__':
  
  try:
    start(sys.argv[1:])
    
  except KeyboardInterrupt:
    print '\n\n^C interrupt, exiting'
    
  except SystemExit:
    pass
    
  except:
    s = sys.exc_info()
    for e in s:
      print "ERROR: " + str(e)
  
  # remove temporary files
  i = 0
  while os.path.exists(temp_dir + str(i)):
    os.remove(temp_dir + str(i))
    i += 1
  os.rmdir(temp_dir)
  
  print '\n *** press enter to exit ***'
  raw_input()
  
