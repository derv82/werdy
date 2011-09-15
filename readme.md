# werdy

## Description

A series of Python scripts for generating, merging, and sorting wordlist files.

## crunch.py

Similar to [crunch](http://sourceforge.net/projects/crunch-wordlist/), this script generates wordlists with every possible combination of specific characters.

* Generates based on minimum and maximum word length.
* Built-in character sets include lower-case, upper-case, numbers, and two symbol sets.
* Accepts custom character sets.
* Option to split output into multiple files of specified byte size.
* Resumes list generation if interrupted.

## phone.py

Generates every phone number for a given region in the U.S.  The script uses a database of "prefixes" (the 3 digits after the area code) to generate mostly valid numbers.

* Looks up region by either city name or area code.
* Has "autopwn" option which looks up location based on IP address and generates phone numbers.
* Customization includes removing area code and setting separators between numbers. Example of formats:
  * (555) 555-1234
  * 555-555-1234
  * 5555551234
  * 555-1234

## sort.py

Sorts given wordlist(s) depending on options.

* Ability to set minimum/maximum word length.
  * Ex: a minimum of 8, maxaximum of 63 would be useful for WPA wordlists.
* Drag-and-drop multiple wordlist files to combine, sort, and remove duplicates.
* Automatically removes duplicate entries. Option to disable this feature.
* Split output file into multiple files of specific byte size.
* "Frequency sort" sorts based on how frequently words appear. Option to display table with word counts.
* Convert entire wordlist to lower-case, upper-case, first-letter-capital, or "elite" text styles.
  * Option to 'make copies' of each word as lower-case, upper-case, first-letter-capital, and 'elite'.
* Strip text to left/right of a separator. Useful for password dumps.
* Filter words containing a filter.
* Ability to strip/keep non-printing characters and leadin/trailing whitespace characters.
* Option to delete input files after they are parsed to save disk space.

