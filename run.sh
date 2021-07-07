#!/usr/bin/env sh

for filename in test/samples/*.pdf; do
  # extract text
  echo "extracting text from $filename..."
  ./main.py -i "$filename" -e A -c TXT -o "test/results/$(basename "$filename")-A.txt"
  ./main.py -i "$filename" -e B -c TXT -o "test/results/$(basename "$filename")-B.txt"
  # extract urls - regex 1
  echo "extracting URLs (regex 1) from $filename..."
  ./main.py -i "$filename" -e A -c URL -o "test/results/$(basename "$filename")-A-R1.txt" -r 1
  ./main.py -i "$filename" -e B -c URL -o "test/results/$(basename "$filename")-B-R1.txt" -r 1
  # extract urls - regex 2
  echo "extracting URLs (regex 2) from $filename..."
  ./main.py -i "$filename" -e A -c URL -o "test/results/$(basename "$filename")-A-R2.txt" -r 2
  ./main.py -i "$filename" -e B -c URL -o "test/results/$(basename "$filename")-B-R2.txt" -r 2
done

# evaluation metrics
./evaluate.py test/results > test/summary.txt
