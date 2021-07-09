#!/usr/bin/env sh

for executor in PDFM GROB; do
  echo "Executor: $executor"
  for filename in test/samples/*.pdf; do
    echo ""
    echo "File: $filename"
    # extract text
    echo "Command: TXT"
    ./main.py -e $executor -c TXT -i "$filename" -o "test/text/$(basename "$filename")-$executor.txt"
    # extract urls
    for regex in 1 2; do
      for cmd in U_ANN U_TXT U_ALL; do
        echo "Command: $cmd, Regex: $regex"
        ./main.py -e "$executor" -c "$cmd" -r "$regex" -i "$filename" -o "test/urls/$(basename "$filename")-$executor-R$regex-$cmd.txt"
      done
    done
  done
done

# evaluation metrics
for cmd in U_ANN U_TXT U_ALL; do
  ./evaluate.py -l test/labels -u test/urls -c $cmd  >test/summary-$cmd.txt
done
