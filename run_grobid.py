#!/usr/bin/env python3

# usage: ./run_grobid.py <filename>

import sys

from bs4 import BeautifulSoup
from grobid_client.grobid_client import GrobidClient

from util import harvest_urls, parse, retain_valid_urls, write_to_file


def run_grobid(file: str) -> list:
    urls = set()
    client = GrobidClient(config_path="./grobid-service/config/config.json")
    [pdf_file, status, result] = client.process_pdf(
        service="processFulltextDocument",
        pdf_file=file,
        generateIDs=False,
        consolidate_header=False,
        consolidate_citations=False,
        include_raw_citations=False,
        include_raw_affiliations=False,
        teiCoordinates=True
    )
    xml_tree = BeautifulSoup(result, 'lxml-xml')
    # links from annotations
    urls.update({parse(x['target']) for x in xml_tree.find_all('ptr', {'target': True})})
    # links from DOIs
    urls.update({parse(f'https://doi.org/{x.text}') for x in xml_tree.find_all('idno', {'type': 'DOI'})})
    # links from text
    text = "\n".join(xml_tree.find_all(text=True))
    for url in harvest_urls(text):
        urls.add(url)
    # concatenate and dedupe
    return sorted(retain_valid_urls(urls))


if __name__ == '__main__':
    links = run_grobid(sys.argv[1])
    # print everything
    write_to_file(links)
