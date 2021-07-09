#!/usr/bin/env sh

for executor in PDFM GROB; do
  echo "Executor: $executor"
  for filename in test/samples/*.pdf; do
    echo ""
    echo "File: $filename"
    op_prefix="test/results/$(basename "$filename")"
    # extract text
    echo "Command: TXT"
    ./main.py -e $executor -c TXT -i "$filename" -o "$op_prefix-$executor-TXT.txt"
    # extract urls
    for cmd in URLS_ANN URLS_TXT URLS_ALL; do
      for regex in 1 2; do
        echo "Command: $cmd, Regex: $regex"
        ./main.py -e $executor -c $cmd -r $regex -i "$filename" -o "$op_prefix-$executor-R$regex-$cmd.txt"
      done
    done
  done
done

# evaluation metrics
./evaluate.py test/results >test/summary.txt
