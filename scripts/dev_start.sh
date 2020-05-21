#!/bin/bash

today=`date +%Y-%m-%d.%H:%M:%S`
nohup python3.6 pittgrub/ --config=config.ini > ./logs/$today.log  &
echo 'PittGrub dev server is up'
echo "Logging to: ./logs/$today.log"

