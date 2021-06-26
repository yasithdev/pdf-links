#!/usr/bin/env python3

import re
import sys
from typing import Union

import requests
import validators

RE_NEWLINES = re.compile(r"\n+")
RE_LINK_PREFIX = re.compile(r"((?<!\s)(http|https|ftp)://)")
RE_LINKS = re.compile(r'(http|ftp|https)://([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?')
RE_PARTIAL_LINKS = re.compile(r'((www)(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?')
RE_DOI = re.compile(r'10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+')
RE_ARXIV_DOI = re.compile(r'\d{4}\.\d{4,5}')


def secure(protocol: str):
    if protocol.startswith("http://"):
        return "https" + protocol[4:]
    return protocol


def retain_valid_urls(s: set, validate_online=False):
    # validator function
    def validator(url):
        try:
            return requests.get(url).ok if validate_online else validators.url(url)
        except:
            return False

    # filter out invalid urls
    valid_urls = set(filter(validator, s))
    return valid_urls


def parse(parts: Union[list, str]):
    if not isinstance(parts, str):
        if len(parts) == 3:
            return parse(f"{parts[0]}://{''.join(parts[1:])}")
        else:
            return parse(''.join(parts))
    url = secure(parts).lower().replace(' ', '').strip(" /\n")
    # doi handling
    if RE_LINKS.fullmatch(url) is not None:
        return url
    if RE_PARTIAL_LINKS.fullmatch(url) is not None:
        return f"https://{url}"
    if RE_DOI.fullmatch(url) is not None:
        return f"https://doi.org/{url}"
    if RE_ARXIV_DOI.fullmatch(url) is not None:
        return f"https://arxiv.org/abs/{url}"
    else:
        return ""


def harvest_urls(text: str):
    # augment text
    text = text + "\n" + RE_NEWLINES.sub("", text) + "\n" + RE_NEWLINES.sub(" ", text)
    # prepend \s to potential urls
    while True:
        proc_text = RE_LINK_PREFIX.sub(r" \1", text)
        if text == proc_text:
            break
        text = proc_text
    # parse and yield url-like
    urls = set()
    for url in RE_LINKS.findall(text):
        urls.add(parse(url))
    for url in RE_PARTIAL_LINKS.findall(text):
        urls.add(parse(url))
    # parse and yield doi-like
    for match in RE_DOI.findall(text):
        urls.add(parse(match))
    # parse and yield arxiv doi-like
    for match in RE_ARXIV_DOI.findall(text):
        urls.add(parse(match))
    return sorted(retain_valid_urls(urls))


def write_to_file(urls: list, file=sys.stdout):
    for url in urls:
        print(url, file=file)
    print(str(len(urls)) + ' URLs discovered')


if __name__ == '__main__':
    print("This file is not meant to be run directly")
