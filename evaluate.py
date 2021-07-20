#!/usr/bin/env python3

import glob
import os.path
from typing import Set

import pandas as pd

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.max_colwidth = None
pd.options.display.expand_frame_repr = False

REGEXES = [3, 4]
EXTRACTORS = ['PDFIUM', 'PDFM', 'GROB']
EPSILON = 1e-10  # small constant to avoid ZeroDivisionError


def get_urls(fp: str) -> Set[str]:
  with open(fp) as f:
    return set(map(lambda x: x.lower().strip(' /'), f.readlines()))


def calculate_metrics(target: Set[str], got: Set[str]) -> dict:
  tp_urls = sorted(got.intersection(target))
  fp_urls = sorted(got.difference(target))
  fn_urls = sorted(target.difference(got))
  # calculate metrics
  [tp, fp, fn] = [*map(len, [tp_urls, fp_urls, fn_urls])]
  precision = tp / max(tp + fp, EPSILON)
  recall = tp / max(tp + fn, EPSILON)
  f_measure = 2 * precision * recall / max(precision + recall, EPSILON)
  return {
    'tp_urls': tp_urls,
    'tp': tp,
    'fp_urls': fp_urls,
    'fp': fp,
    'fn_urls': fn_urls,
    'fn': fn,
    'p': precision,
    'r': recall,
    'f': f_measure
  }


def calculate_agg_metrics(metrics: dict, cmd: str) -> dict:
  def agg(exc: str):
    r = {
      'tp_urls': {},
      'tp': 0,
      'fp_urls': {},
      'fp': 0,
      'fn_urls': {},
      'fn': 0,
      'mac_p': 0,
      'mac_r': 0,
      'mac_f': 0,
      'mic_p': 0,
      'mic_r': 0,
      'mic_f': 0
    }
    for sample in metrics:
      for measure in metrics[sample][exc]:
        if measure in ['tp_urls', 'fp_urls', 'fn_urls']:
          r[measure][sample] = metrics[sample][exc][measure]
        elif measure in ['tp', 'fp', 'fn']:
          r[measure] += metrics[sample][exc][measure]
        elif measure in ['p', 'r', 'f']:
          # update macro average metrics
          r[f'mac_{measure}'] += (metrics[sample][exc][measure]) / len(metrics)
    # update micro average metrics
    r['mic_p'] = r['tp'] / max(r['tp'] + r['fp'], EPSILON)
    r['mic_r'] = r['tp'] / max(r['tp'] + r['fn'], EPSILON)
    r['mic_f'] = 2 * r['mic_p'] * r['mic_r'] / max(r['mic_p'] + r['mic_r'], EPSILON)
    agg_metrics[exc] = r

  agg_metrics = {}
  if cmd == "U_ANN":
    # aggregate annotated URL metrics
    agg(cmd)
  else:
    for extractor in EXTRACTORS:
      if extractor == "PDFIUM":
        agg(f"{extractor}-{cmd}")
      else:
        # aggregate fulltext URL metrics
        for regex in REGEXES:
          agg(f"{extractor}-R{regex}-{cmd}")

  return agg_metrics


def clean(url: str) -> str:
  return url.strip().lower().rstrip('.,/?')


def run(labels_dir: str, urls_dir: str, cmd: str, out=None):
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
        if extractor == "PDFIUM":
          exc = f"{extractor}-{cmd}"
          extracted_urls = set(map(clean, get_urls(f'{urls_dir}/{file_name}-{exc}.txt')))
          metrics[exc] = calculate_metrics(true_urls, extracted_urls)
        else:
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
    print(df[['tp', 'fp', 'fn', 'p', 'r', 'f']], end="\n\n")

  # calculate and print aggregate metrics
  print('=================\naggregate metrics\n=================')
  agg_metrics = calculate_agg_metrics(all_metrics, cmd)
  df_agg = pd.DataFrame.from_dict(agg_metrics, orient='index').sort_index()
  print(df_agg[['tp', 'fp', 'fn', 'mac_p', 'mac_r', 'mac_f', 'mic_p', 'mic_r', 'mic_f']], end="\n\n")

  # print which urls are tp, fp, fn, and tn of each method
  if out:
    table = pd.DataFrame(columns=['method', 'metric', 'sample', 'url'])
    for extractor in sorted(agg_metrics.keys()):
      data = agg_metrics[extractor]
      # transform into table format
      for metric in ['tp', 'fp', 'fn']:
        for sample in data[f'{metric}_urls']:
          for url in data[f'{metric}_urls'][sample]:
            table.loc[len(table)] = [extractor, metric, sample, url]
    table = table.set_index(['method', 'metric', 'sample'])
    table.to_csv(out)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Link Extractor Evaluator')
  parser.add_argument('-l', metavar="LABELS_PATH", required=True, help="path to labels directory", type=str)
  parser.add_argument('-u', metavar="URLS_PATH", required=True, help="path to urls directory", type=str)
  parser.add_argument('-c', metavar="COMMAND", required=True, help="name of command", type=str)
  parser.add_argument('-o', metavar="OUT_CSV", required=False, help="path to output csv", type=str)
  args = parser.parse_args()
  if args.o:
    run(str(args.l).rstrip('/ '), str(args.u).rstrip('/ '), str(args.c), out=str(args.o))
  else:
    run(str(args.l).rstrip('/ '), str(args.u).rstrip('/ '), str(args.c))
