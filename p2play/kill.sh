#!/usr/bin/env bash

for thing in $(ps ux | grep python3 | grep -v grep | awk '{print $2}'); do
    echo "Killing $thing"
    kill -9 $thing
done
