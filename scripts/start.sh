#!/bin/bash

today=`date +%Y-%m-%d.%H:%M:%S`
nohup python3.6 pittgrub/ --config=config.ini > ./logs/$today.log  &
echo 'PittGrub server is up'

