#!/usr/bin/env python3

import glob
import os.path
import sys
from typing import Set

import pandas as pd


def get_urls(fp: str) -> Set[str]:
  with open(fp) as f:
    return set(map(lambda x: x.lower().strip(' /'), f.readlines()))


def calculate_metrics(target: Set[str], got: Set[str]) -> dict:
  tp = len(got.intersection(target))
  fn = len(got.difference(target))
  fp = len(target.difference(got))
  tn = 0  # because ground truth only has valid URLs
  return {'tp': tp, 'fn': fn, 'fp': fp, 'tn': tn}


def calculate_agg_metrics(metrics: dict) -> dict:
  agg_metrics = {}
  for method in ['PDFM', 'GROB']:
    for option in ['R1', 'R2']:
      exc = f"{method}-{option}-URLS_ALL"
      r = {'tp': 0, 'fn': 0, 'fp': 0, 'tn': 0}
      for sample in metrics:
        for measure in r:
          r[measure] += metrics[sample][exc][measure]
      r['tpr'] = r['tp'] / (r['tp'] + r['fn'])
      r['fpr'] = r['fp'] / (r['fp'] + r['tn'])
      agg_metrics[exc] = r
  return agg_metrics


def run(results_dir: str):
  all_metrics = {}

  # calculate and print metrics for each file
  print('\n===============\nmetrics by file\n===============')
  for file_name in sorted(glob.glob(f"{results_dir.rstrip('/ ')}/*-true.txt")):
    file_name = file_name[:-9]
    true_urls = get_urls(f'{file_name}-true.txt')
    metrics = {}
    # get URLs from each method
    for extractor in ['PDFM', 'GROB']:
      for option in ['R1', 'R2']:
        for cmd in ['URLS_ANN', 'URLS_ALL']:
          exc = f"{extractor}-{option}-{cmd}"
          extracted_urls = get_urls(f'{file_name}-{exc}.txt')
          metrics[exc] = calculate_metrics(true_urls, extracted_urls)
    # save metrics
    base_name = os.path.basename(file_name)
    all_metrics[base_name] = metrics
    # print metric
    df = pd.DataFrame.from_dict(metrics, orient='index').sort_index()
    df.index.name = base_name
    print(df)

  # calculate and print aggregate metrics
  print('\n=================\naggregate metrics\n=================')
  agg_metrics = calculate_agg_metrics(all_metrics)
  df_agg = pd.DataFrame.from_dict(agg_metrics, orient='index').sort_index()
  print(df_agg)


if __name__ == '__main__':
  run(sys.argv[1])
