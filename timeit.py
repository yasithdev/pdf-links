#!/usr/bin/env python3

import glob
import re
import pandas as pd

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.max_colwidth = None
pd.options.display.expand_frame_repr = False


def run(fp: str, op: str):
  # read from all files
  data = []
  files = glob.glob(f'{fp}/timing-run-*.txt')
  for n, file in enumerate(files):
    with open(file) as f:
      lines = f.readlines()
    for i in range(0, len(lines) - 1, 2):
      info = lines[i].strip().rsplit('/')[-1]
      item = {'file': info.split(' [', 1)[0], 'n': n}
      for m in re.finditer(r'\[(\w+):\s(\w+)\]', info):
        item[m.group(1).lower()] = m.group(2)
      item['value'] = float(lines[i + 1].strip().split(' ')[2])
      data.append(item)

  # create dataframe
  df = pd.DataFrame(data).fillna('-')

  # extract specific slices (regardless of file)
  val_col = ['value']
  ann_col = []
  txt_col = ['executor']
  url_col = ['executor', 'regex']

  print('\n============================\nOVERALL\n============================')
  print('\n=====U_ANN=====')
  print(df[df['command'] == 'U_ANN'][ann_col + val_col].mean().sort_index())
  print('\n=====TXT=====')
  print(df[df['command'] == 'TXT'][txt_col + val_col].groupby(txt_col).mean().sort_index())
  print('\n=====U_TXT=====')
  print(df[df['command'] == 'U_TXT'][url_col + val_col].groupby(url_col).mean().sort_index())
  print('\n=====U_ALL=====')
  print(df[df['command'] == 'U_ALL'][url_col + val_col].groupby(url_col).mean().sort_index())

  # extract specific slices (with files)
  val_col = ['value']
  ann_col = ['file']
  txt_col = ['file', 'executor']
  url_col = ['file', 'executor', 'regex']

  print('\n============================\nPER FILE\n============================')
  print('\n=====U_ANN=====')
  print(df[df['command'] == 'U_ANN'][ann_col + val_col].groupby(ann_col).mean().sort_index())
  print('\n=====TXT=====')
  print(df[df['command'] == 'TXT'][txt_col + val_col].groupby(txt_col).mean().sort_index())
  print('\n=====U_TXT=====')
  print(df[df['command'] == 'U_TXT'][url_col + val_col].groupby(url_col).mean().sort_index())
  print('\n=====U_ALL=====')
  print(df[df['command'] == 'U_ALL'][url_col + val_col].groupby(url_col).mean().sort_index())


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Timing Summary Generator')
  parser.add_argument('-i', metavar="INPUT_PATH", required=True, help="path to timing information directory", type=str)
  parser.add_argument('-o', metavar="OUTPUT_PATH", required=False, help="path (with prefix) to output csv", type=str)
  args = parser.parse_args()
  run(str(args.i).rstrip('/ '), args.o)
