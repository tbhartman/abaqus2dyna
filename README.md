abaqus2dyna
============

[![Build Status](https://travis-ci.com/tbhartman/abaqus2dyna.svg?branch=master)](https://travis-ci.com/tbhartman/abaqus2dyna)
[![Coverage Status](https://coveralls.io/repos/github/tbhartman/abaqus2dyna/badge.svg?branch=dev)](https://coveralls.io/github/tbhartman/abaqus2dyna?branch=dev)
[![PyPI version](https://badge.fury.io/py/abaqus2dyna.svg)](https://badge.fury.io/py/abaqus2dyna)

abaqus2dyna is a script to convert, in a limited fashion, Abaqus keyword input
files to LS-DYNA keyword input files.  It is currently very limited.  See
`example.inp` for an example Abaqus file that can be converted.

**Note**: test coverage is virtually nil, and the code is likely difficult to
follow.  I may try to improve it, but feel free to modify and make a pull
request.  As of October 2018, I have at least set up some *very* basic tests,
but manually testing is still required until I enhance the test suite.


License
=======

abaqusy2dyna is free software and licensed under the MIT License.


Installation
============

`pip install abaqus2dyna`


Instructions
============

`abaqus2dyna.py INPUT -o output`


Features
========

The goal is to convert the nodes/elements/sets of an Abaqus assembly
to an equivalent input file for LS-DYNA.  The user is responsible
to convert steps/materials/etc.

Info
====

Source code:
https://github.com/tbhartman/abaqus2dyna
