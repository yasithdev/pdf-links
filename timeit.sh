#!/usr/bin/env sh

for i in $(seq 1 10); do
  echo "round $i of 10"
  sh -c "make | awk '/^File: / || /^generated in/' | tee test/timing-run-$i.txt"
done