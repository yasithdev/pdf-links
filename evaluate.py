#!/usr/bin/env python3

import glob
import os.path
from typing import Set

import pandas as pd

REGEXES = [1, 2, 3, 4]
EXTRACTORS = ['PDFM', 'GROB']


def get_urls(fp: str) -> Set[str]:
  with open(fp) as f:
    return set(map(lambda x: x.lower().strip(' /'), f.readlines()))


def calculate_metrics(target: Set[str], got: Set[str]) -> dict:
  tp = len(got.intersection(target))
  fn = len(target.difference(got))
  fp = len(got.difference(target))
  tn = 0  # because ground truth only has valid URLs
  return {'tp': tp, 'fn': fn, 'fp': fp, 'tn': tn}


def calculate_agg_metrics(metrics: dict, cmd: str) -> dict:
  def agg(exc: str):
    r = {'tp': 0, 'fn': 0, 'fp': 0, 'tn': 0}
    for sample in metrics:
      for measure in r:
        r[measure] += metrics[sample][exc][measure]
    r['tpr'] = r['tp'] / max(r['tp'] + r['fn'], 1)  # lower bound to avoid ZeroDivisionError
    r['fpr'] = r['fp'] / max(r['fp'] + r['tn'], 1)  # lower bound to avoid ZeroDivisionError
    agg_metrics[exc] = r

  agg_metrics = {}
  if cmd == "U_ANN":
    # aggregate annotated URL metrics
    agg(cmd)
  else:
    for extractor in EXTRACTORS:
      # aggregate fulltext URL metrics
      for regex in REGEXES:
        agg(f"{extractor}-R{regex}-{cmd}")

  return agg_metrics


def clean(url: str) -> str:
  return url.strip().lower().rstrip('.,/?')


def run(labels_dir: str, urls_dir: str, cmd: str):
  all_metrics = {}

  # calculate and print metrics for each file
  print('===============\nmetrics by file\n===============')
  for full_path in sorted(glob.glob(f"{labels_dir}/*.pdf.txt")):
    file_name = os.path.basename(full_path[:-4])
    true_urls = set(map(clean, get_urls(f'{labels_dir}/{file_name}.txt')))
    metrics = {}
    if cmd == "U_ANN":
      # get annotated URL metric
      exc = cmd
      extracted_urls = set(map(clean, get_urls(f'{urls_dir}/{file_name}-{exc}.txt')))
      metrics[exc] = calculate_metrics(true_urls, extracted_urls)
    else:
      # get URLs from each method
      for extractor in EXTRACTORS:
        # get fulltext URL metrics
        for regex in REGEXES:
          exc = f"{extractor}-R{regex}-{cmd}"
          extracted_urls = set(map(clean, get_urls(f'{urls_dir}/{file_name}-{exc}.txt')))
          metrics[exc] = calculate_metrics(true_urls, extracted_urls)
    # save metrics
    all_metrics[file_name] = metrics
    # print metric
    df = pd.DataFrame.from_dict(metrics, orient='index').sort_index()
    df.index.name = f"{file_name} ({len(true_urls)} URLs)"
    print(df, end="\n\n")

  # calculate and print aggregate metrics
  print('=================\naggregate metrics\n=================')
  agg_metrics = calculate_agg_metrics(all_metrics, cmd)
  df_agg = pd.DataFrame.from_dict(agg_metrics, orient='index').sort_index()
  print(df_agg)

  # TODO calculate and print which urls are tp, fp, fn, and tn


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Link Extractor Evaluator')
  parser.add_argument('-l', metavar="LABELS_PATH", required=True, help="path to labels directory", type=str)
  parser.add_argument('-u', metavar="URLS_PATH", required=True, help="path to urls directory", type=str)
  parser.add_argument('-c', metavar="COMMAND", required=True, help="name of command", type=str)
  args = parser.parse_args()
  run(str(args.l).rstrip('/ '), str(args.u).rstrip('/ '), str(args.c))
