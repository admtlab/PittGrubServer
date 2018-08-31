#!/bin/bash

today=`date +%Y-%m-%d.%H:%M:%S`
logfile=$(awk -F "=" '/log/ {print $2}' config.ini | tr -d '[:space:]')
logfile=${logfile:="./logs/$today.log"}
nohup python3 pittgrub/ --config=config.ini > $logfile  &
echo 'PittGrub server is up'
echo "Logging to: $logfile"

