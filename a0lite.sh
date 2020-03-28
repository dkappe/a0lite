#!/bin/bash

BASEDIR=$(dirname "$0")
cd $BASEDIR
exec python engine.py
