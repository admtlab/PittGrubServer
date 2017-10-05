#!/bin/bash

lsof -ti :21008 | xargs --no-run-if-empty kill -9
echo "PittGrub server is down"

