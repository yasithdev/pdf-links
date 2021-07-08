#!/usr/bin/env python3

import glob
import os.path
import sys
from typing import Set

import pandas as pd


def get_links(fp: str) -> Set[str]:
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
  for method in ['A', 'B']:
    for regex_mode in ['R1', 'R2']:
      exc = f"{method}-{regex_mode}"
      r = {'tp': 0, 'fn': 0, 'fp': 0, 'tn': 0}
      for sample in metrics:
        for measure in r:
          r[measure] += metrics[sample][exc][measure]
      r['tpr'] = r['tp'] / (r['tp'] + r['fn'])
      r['fpr'] = r['fp'] / (r['fp'] + r['tn'])
      agg_metrics[exc] = r
  return agg_metrics


def run(results_dir: str):
  metrics = {}

  for file_name in sorted(glob.glob(f"{results_dir.rstrip('/ ')}/*-true.txt")):
    file_name = file_name[:-9]

    # get links from each method
    true_links = get_links(f'{file_name}-true.txt')
    a_r1_links = get_links(f'{file_name}-A-R1.txt')
    a_r2_links = get_links(f'{file_name}-A-R2.txt')
    b_r1_links = get_links(f'{file_name}-B-R1.txt')
    b_r2_links = get_links(f'{file_name}-B-R2.txt')

    # calculate metrics
    metrics[os.path.basename(file_name)] = {
      'A-R1': calculate_metrics(true_links, a_r1_links),
      'A-R2': calculate_metrics(true_links, a_r2_links),
      'B-R1': calculate_metrics(true_links, b_r1_links),
      'B-R2': calculate_metrics(true_links, b_r2_links)
    }

  # calculate aggregate metrics
  agg_metrics = calculate_agg_metrics(metrics)

  # print calculated metrics
  print('\n===============\nmetrics by file\n===============')
  for f in metrics:
    df = pd.DataFrame.from_dict(metrics[f], orient='index')
    df.index.name = f
    print(df)

  # print aggregate metrics
  print('\n=================\naggregate metrics\n=================')
  df_agg = pd.DataFrame.from_dict(agg_metrics, orient='index')
  print(df_agg)


if __name__ == '__main__':
  run(sys.argv[1])
