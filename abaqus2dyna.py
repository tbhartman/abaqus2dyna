#!/usr/bin/python3 -i

# abaqus2dyna.by
# 
# Copyright 2011 Tim Hartman <tbhartman@gmail.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

version='alpha'

import argparse
import numpy as np
import re
from collections import *
import datetime
import sys
import tempfile
import console
import fea
import fea.abaqus
import fea.lsdyna

terminal_width,_ = console.getTerminalSize()

# argument parsing definitions

parser = argparse.ArgumentParser(prog='abaqus2dyna',
                                 description='Translate Abaqus to LS-DYNA')
parser.add_argument('input',
                    metavar='INPUT',
                    help='Abaqus keyword file (limit one)',
                    nargs=1,
                    type=argparse.FileType('r'))
parser.add_argument('-o', '--output',
                    dest='output',
                    metavar='OUTPUT',
                    help='LS-DYNA keyword file output location',
                    type=argparse.FileType('w'))
parser.add_argument('-s', '--stats',
                    action='store_true',
                    dest='stats',
                    help='Show input file stats only')
parser.add_argument('-V', '--verbose',
                    action='store_true',
                    dest='verbose',
                    help='Be verbose')
parser.add_argument('-v', '--version',
                    action='version',
                    version='%(prog)s ' + version)
args = parser.parse_args()


inp = fea.abaqus.Parse(args.input[0],verbosity=args.verbose)

if args.stats:
    print(inp.counter['line'])

if args.verbose:
    print('I was being verbose.')
