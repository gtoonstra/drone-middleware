#!/bin/bash

export IVYBUS=127.255.255.255:2010
export PYTHONPATH=/work/drone-middleware/protocol/python
export PAPARAZZI_SRC=/work/paparazzi
export PAPARAZZI_HOME=/work/paparazzi

python pprz_ground.py 1

