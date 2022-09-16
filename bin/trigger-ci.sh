#!/bin/bash
# Add the bin folder to your PATH to make this file executable so you can conveniently trigger
# this convenience script instead of add, commit and push individually
# FIXME: allow actual commit message as an optional parameter 

auto_datetime=$(date '+%Y-%m-%d %H:%M:%S')
python run_tests.py
test=$?
if [ $test -eq 0 ] 
then
    echo 'All tests passed.. proceeding to commit then push'
    git add -A
    git commit -m "auto msg: $auto_datetime $1"
    git push
else
    echo 'Aborting commit'
fi