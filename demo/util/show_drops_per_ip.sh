#!/bin/bash

for i in $( seq $HOSTS_NUM )
do
	echo Drops for 10.0.0.$i = `grep "10.0.0.$i failed, skipping" *.log | wc -l`
done
