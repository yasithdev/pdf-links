#!/usr/bin/env python3

import glob
import os
import sys

from run_grobid import run_grobid
from run_pdfminer import run_pdfminer
from run_pypdf2 import run_pypdf2
from util import write_to_file


def run(input_dir: str, output_dir: str):
    for input_path in sorted(glob.glob(f"{input_dir.rstrip('/ ')}/*")):
        # ignore non pdfs
        if input_path[-3:].lower() != "pdf":
            continue
        print(f'\nProcessing {input_path}...')

        # build output path
        basename = os.path.basename(input_path)

        # PyPDF2
        with open(f"{output_dir.rstrip('/ ')}/{basename}-pypdf2.txt", "w") as out:
            pypdf2_links = run_pypdf2(input_path)
            write_to_file(pypdf2_links, file=out)
            print('[PyPDF2] Done!')

        # PDFMiner
        with open(f"{output_dir.rstrip('/ ')}/{basename}-pdfminer.txt", "w") as out:
            pdfx_links = run_pdfminer(input_path)
            write_to_file(pdfx_links, file=out)
            print('[PDFMiner] Done!')

        # PyPDF2+PDFMiner
        with open(f"{output_dir.rstrip('/ ')}/{basename}-pypdf2+pdfminer.txt", "w") as out:
            pypdf2_and_pdfx_links = sorted({*pypdf2_links, *pdfx_links})
            write_to_file(pypdf2_and_pdfx_links, file=out)
            print(f'[PyPDF2+PDFMiner] Done!')

        # GROBID
        with open(f"{output_dir.rstrip('/ ')}/{basename}-grobid.txt", "w") as out:
            grobid_links = run_grobid(input_path)
            write_to_file(grobid_links, file=out)
            print(f'[GROBID] Done!')


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
