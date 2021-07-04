#!/usr/bin/env sh

for filename in resources/samples/*.pdf; do
  # extract text
  echo "extracting text from $filename..."
  ./main.py -i "$filename" -e A -c TXT -o "$filename"-A.txt
  ./main.py -i "$filename" -e B -c TXT -o "$filename"-B.txt
  # extract urls - regex 1
  echo "extracting URLs (regex 1) from $filename..."
  ./main.py -i "$filename" -e A -c URL -o "$filename"-A-R1.txt -r 1
  ./main.py -i "$filename" -e B -c URL -o "$filename"-B-R1.txt -r 1
  # extract urls - regex 2
  echo "extracting URLs (regex 2) from $filename..."
  ./main.py -i "$filename" -e A -c URL -o "$filename"-A-R2.txt -r 2
  ./main.py -i "$filename" -e B -c URL -o "$filename"-B-R2.txt -r 2
done
