#!/bin/bash

lsof -ti :21000 | xargs --no-run-if-empty kill -9
echo "PittGrub dev server is down"

