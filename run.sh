#!/usr/bin/env sh

for filename in test/samples/*.pdf; do
  echo ""
  echo "File: $filename"
  # extract annotations
  echo "Command: U_ANN"
  ./main.py -c U_ANN -i "$filename" -o "test/urls/$(basename "$filename")-U_ANN.txt"
  for executor in PDFM GROB; do
    # extract text
    echo "Command: TXT [Executor: $executor]"
    ./main.py -c TXT -e $executor -i "$filename" -o "test/text/$(basename "$filename")-$executor.txt"
    # extract urls from text
    for cmd in U_TXT U_ALL; do
      for regex in 1 2 3 4; do
        echo "Command: $cmd [Executor: $executor] [Regex: $regex]"
        ./main.py -c "$cmd" -e "$executor" -r "$regex" -i "$filename" -o "test/urls/$(basename "$filename")-$executor-R$regex-$cmd.txt"
      done
    done
  done
done

# evaluation metrics
for cmd in U_ANN U_TXT U_ALL; do
  ./evaluate.py -l test/labels -u test/urls -c $cmd >test/summary-$cmd.txt
done
