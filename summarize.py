#!/usr/bin/env python3

import csv
import glob
import os

import pandas as pd

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.max_colwidth = None
pd.options.display.expand_frame_repr = False

if __name__ == '__main__':
  urls = {}
  for path in sorted(glob.glob("test/summary-*.csv")):
    exc = os.path.basename(path)[8:-4]
    with open(path) as f:
      csv_reader = csv.reader(f)
      next(csv_reader)
      for [metric, sample, url] in csv_reader:

        if metric == 'tp':
          v = 'Y'
        elif metric == 'fn':
          v = 'N'
        elif metric == 'fp':
          v = 'X'

        if url in urls:
          urls[url][exc] = v
          if sample not in urls[url]['source']:
            urls[url]['source'].append(sample)
        else:
          urls[url] = {exc: v, 'source': [sample]}
  df = pd.DataFrame.from_dict(urls, orient='index')
  df = df.sort_index().fillna('-')
  df.to_csv('test/url-summary.csv')
