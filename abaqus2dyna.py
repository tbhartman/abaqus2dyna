#!/usr/bin/python -i

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

version='0.0.1'

import argparse

parser = argparse.ArgumentParser(prog='abaqus2dyna', description='Translate Abaqus to LS-DYNA')
parser.add_argument('input', metavar='INPUT', help='Abaqus keyword file (limit one)', nargs=1, type=argparse.FileType('r'))
parser.add_argument('-o, --output', dest='output', metavar='OUTPUT', help='LS-DYNA keyword file output location', type=argparse.FileType('w'))
parser.add_argument('-v, --version', action='version', version='%(prog)s ' + version)
args = parser.parse_args()


