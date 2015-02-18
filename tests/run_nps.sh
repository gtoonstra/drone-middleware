#!/bin/bash

export PAPARAZZI_SRC=/work/paparazzi
export PAPARAZZI_HOME=/work/paparazzi

/work/paparazzi/sw/simulator/pprzsim-launch -a Suave -t nps -b 127.255.255.255:2011

