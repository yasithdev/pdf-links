#!/usr/bin/env python3

import glob
import os
import sys

import pandas as pd


def run(labels_dir: str, results_dir: str):
    metrics = []

    for input_path in sorted(glob.glob(f"{labels_dir.rstrip('/ ')}/*")):
        # ignore non pdfs
        if input_path[-11:].lower() != "-actual.txt":
            continue
        print(f'Processing {input_path}...')

        # target urls
        urls_fn = os.path.basename(input_path[:-11])
        with open(f'{labels_dir}/{urls_fn}-actual.txt', 'r') as f:
            target_urls = set(f.readlines())

        # pypdf2 urls
        with open(f'{results_dir}/{urls_fn}-pypdf2.txt', 'r') as f:
            pypdf2_urls = set(f.readlines())

        # pdfminer urls
        with open(f'{results_dir}/{urls_fn}-pdfminer.txt', 'r') as f:
            pdfx_urls = set(f.readlines())

        # pypdf2+pdfminer urls
        with open(f'{results_dir}/{urls_fn}-pypdf2+pdfminer.txt', 'r') as f:
            pypdf2_pdfx_urls = set(f.readlines())

        # grobid urls
        with open(f'{results_dir}/{urls_fn}-grobid.txt', 'r') as f:
            grobid_urls = set(f.readlines())

        # calculate metrics

        # PyPDF2
        hits = len(pypdf2_urls.intersection(target_urls))
        misses = len(target_urls.difference(pypdf2_urls))
        extras = len(pypdf2_urls.difference(target_urls))
        metrics.append([urls_fn, len(target_urls), "pypdf2", hits, misses, extras])

        # PDFMiner
        hits = len(pdfx_urls.intersection(target_urls))
        misses = len(target_urls.difference(pdfx_urls))
        extras = len(pdfx_urls.difference(target_urls))
        metrics.append([urls_fn, len(target_urls), "pdfminer", hits, misses, extras])

        # PyPDF2 + PDFMiner
        hits = len(pypdf2_pdfx_urls.intersection(target_urls))
        misses = len(target_urls.difference(pypdf2_pdfx_urls))
        extras = len(pypdf2_pdfx_urls.difference(target_urls))
        metrics.append([urls_fn, len(target_urls), "pypdf2_pdfminer", hits, misses, extras])

        # GROBID
        hits = len(grobid_urls.intersection(target_urls))
        misses = len(target_urls.difference(grobid_urls))
        extras = len(grobid_urls.difference(target_urls))
        metrics.append([urls_fn, len(target_urls), "grobid", hits, misses, extras])

    print('Done!\n')

    df = pd.DataFrame(metrics, columns=['File', 'Count', 'Model', 'Hits', 'Misses', 'Extras']).set_index(['File', 'Count', 'Model'])
    print(df)
    df.to_csv(f'{results_dir}/summary.csv')


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
