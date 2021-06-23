#!/usr/bin/env python3

# usage: ./run_pypdf2.py <filename>

import sys

from PyPDF2.pdf import PdfFileReader, PageObject

from util import parse, retain_valid_urls, write_to_file

ANNOTS = '/Annots'
URI = '/URI'
A = '/A'


def run_pypdf2(path: str) -> list:
    urls = set()
    with open(path, "rb") as file:
        pdf = PdfFileReader(file)
        page: PageObject
        for page in pdf.pages:
            if ANNOTS in page.keys():
                for a in page[ANNOTS]:
                    u = a.getObject()
                    if A in u.keys() and URI in u[A].keys():
                        url = parse(u[A][URI])
                        urls.add(url)
    # concatenate and dedupe
    return sorted(retain_valid_urls(urls))


if __name__ == '__main__':
    links = run_pypdf2(sys.argv[1])
    # print everything
    write_to_file(links)
