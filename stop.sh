#!/bin/bash

lsof -ti :21000 | xargs kill -9
echo "PittGrub server is down"

