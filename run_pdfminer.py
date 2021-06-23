#!/usr/bin/env python3

# usage: ./run_pdfminer.py <filename>

import sys

from pdfminer.high_level import extract_text

from util import harvest_urls, retain_valid_urls, write_to_file


def run_pdfminer(path: str) -> list:
    urls = set()
    with open(path, "rb") as file:
        text = extract_text(file)
        for url in harvest_urls(text):
            urls.add(url)
    # concatenate and dedupe
    return sorted(retain_valid_urls(urls))


if __name__ == '__main__':
    links = run_pdfminer(sys.argv[1])
    # print everything
    write_to_file(links)
