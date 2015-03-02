#!/bin/bash -l

HERMES_DIR=$1
HERMES_VENV=$2

source $HERMES_VENV/bin/activate
cd $HERMES_DIR
python setup.py develop
deactivate
