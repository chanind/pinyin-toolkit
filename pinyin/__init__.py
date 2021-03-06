import sys
import os

# Set up the path Python uses to look for import packages to
# include the 3rd-party dependencies we have folded in
import utils

# Sanity prevails from this point:
sys.path.append(utils.toolkitdir("pinyin", "vendor", "python27"))
sys.path.append(utils.toolkitdir("pinyin", "vendor", "cjklib"))
sys.path.append(utils.toolkitdir("pinyin", "vendor", "sqlalchemy", "lib"))

import config
import db
import dictionary
import languages
import logger
import media
import meanings
import mocks
import model
import numberutils
import statistics
import transformations

#import anki  # Don't import the anki submodule because it imports lots of anki stuff,
              # and if we're running from the command line it won't be available
#import forms # Same goes for this guy

# Expose package metadata via the quasi-standard __version__
# attribute: http://www.python.org/dev/peps/pep-0008/
__version_info__ = ('0', '7', '0')
__version__ = '.'.join(__version_info__)
