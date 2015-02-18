#!/bin/bash

export IVYBUS=127.254.254.254:2011
export PYTHONPATH=/work/drone-middleware/protocol/python
export PAPARAZZI_SRC=/work/paparazzi
export PAPARAZZI_HOME=/work/paparazzi

python pprz_vehicle.py

