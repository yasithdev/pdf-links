#!/usr/bin/env python3
import re
from typing import Optional, List, Set

import bs4


# ======================================================================================================================
# REGEX CONFIGURATION
# ======================================================================================================================


class UrlRegex:
  """
  Configuration class for URL regular expressions
  """

  @staticmethod
  def __get__(option: int):
    if option == 1:
      # based on https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string
      return [
        re.compile(r'((https?|ftp)://([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)', re.I),
        re.compile(r'(([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)', re.I),
        re.compile(r'((www(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)', re.I)
      ]
    elif option == 2:
      # based on http://www.faqs.org/rfcs/rfc2396.html
      return [
        re.compile(r'((https?|ftp)://([^\s@/?#]+\.)+[a-z]{2,}(/[^\s?#]+)?(\?[^\s#]+)?(#\S)?)', re.I),
        re.compile(r'(([^\s@/?#]+\.)+[a-z]{2,}(/[^\s?#]+)?(\?[^\s#]+)?(#\S)?)', re.I),
        re.compile(r'(www\.([^\s@/?#]+\.)*[a-z]{2,}(/[^\s?#]+)?(\?[^\s#]+)?(#\S)?)', re.I)
      ]
    else:
      raise NotImplementedError('Option Does Not Exist!')

  def __init__(self, option: int, safe=True):
    idx_f = 0
    idx_p = 1 if not safe else 2
    regex = UrlRegex.__get__(option)
    self.FULL_URL = regex[idx_f]
    self.PARTIAL_URL = regex[idx_p]
    self.NEWLINE = re.compile(r"\n+")
    with open('blacklist.txt', 'r', encoding='utf-8') as f:
      self.BLACKLIST = re.compile(r".*(" + r"|".join(map(lambda x: f'{x.strip()}', f.readlines())) + r").*", re.I)


# ======================================================================================================================
# UTILITY FUNCTIONS
# ======================================================================================================================

class Util:
  """
  Helper functions to perform link extraction from text

  """

  @staticmethod
  def canonicalize_url(url: str, regex: UrlRegex) -> Optional[str]:
    """
    Canonicalize a given URL.
    Returns None for malformed URLs

    :return: Canonical URL (or None)
    """
    # sanitize URL
    url = url.lower().strip(" /\n")
    # if full URL, return HTTPS/FTP URL
    match = regex.FULL_URL.search(url)
    if match is not None:
      curl = match.group(0).replace("http://", "https://", 1)
      return curl
    # if partial URL, return HTTPS URL
    match = regex.PARTIAL_URL.search(url)
    if match is not None:
      curl = f"https://{match.group(0)}"
      return curl
    # if neither, return None
    return None

  @staticmethod
  def get_valid_urls(s: Set[Optional[str]], regex: UrlRegex, online: bool = False) -> Set[str]:
    """
    Return the subset of valid URLs from a given set of URLs

    :param s: set of URLs to pick valid URLs from
    :param regex: configuration to use
    :param online: if True, send a HEAD request and check for 200 OK. Else (default) validate syntactically
    :return: subset of valid URLs
    """

    def validator(url):
      # validate against URL blacklist
      if regex.BLACKLIST.search(url) is not None:
        ok = False
      else:
        # validate URL integrity
        try:
          if online:
            import requests
            ok = requests.head(url).ok
          else:
            import validators
            ok = validators.url(url)
        except:
          ok = False
      # print(f"({'✓' if ok else 'x'}){url}")
      return ok

    return set(filter(validator, s.difference({None})))

  @staticmethod
  def harvest_urls(text: str, regex: UrlRegex) -> Set[str]:
    """
    Extract URLs from full text

    :param text: full text input
    :param regex: configuration to use
    :return: set of URLs found in full text
    """
    from unidecode import unidecode
    # simplify unicode characters in text
    text = unidecode(text)
    # augment text
    text = text + "\n" + regex.NEWLINE.sub("", text) + "\n"
    # parse and yield urls
    urls = set()

    def find_urls(v: str, r: re.Pattern, i: int) -> List[str]:
      for m in r.findall(v):
        yield Util.canonicalize_url(m[i], regex)

    urls = urls.union(find_urls(text, regex.FULL_URL, 0))
    urls = urls.union(find_urls(text, regex.PARTIAL_URL, 0))
    # get valid urls from the set
    return Util.get_valid_urls(urls, regex)

  @staticmethod
  def has_match(x: str, pool: Set[str]):
    """
    Return whether the URL x has sub/super string matches in pool
    :param x: URL to check for uniqueness
    :param pool: pool of URLs to check uniqueness against
    :return: True if url is unique, else False
    """
    return any((x[8:] in y[8:]) or (y[8:] in x[8:]) for y in pool)

  @staticmethod
  def pick_uniq_urls(pool: Set[str], prefer_long=False):
    """
    Return a subset of unique URLs from pool (favors shorter URLs by default)

    :param pool: pool of URLs
    :param prefer_long: Whether to favor short URLs (default) or long URLs
    :return: subset of unique URLs
    """
    uniq_urls = set()
    for url in sorted(pool, key=len, reverse=prefer_long):
      if not Util.has_match(url, uniq_urls):
        uniq_urls.add(url)
    return uniq_urls

  @staticmethod
  def pick_new_urls(pool: Set[str], blacklist: Set[str]) -> Set[str]:
    """
    Return a subset of URLs from pool that are not in the blacklist

    :param pool: pool of URLs
    :param blacklist: set of URLs to avoid
    :return: subset of new URLs
    """
    # return subset of uniq_urls that are not in blacklist
    return set(url for url in pool if not Util.has_match(url, blacklist))


# ======================================================================================================================
# PYPDF2 FUNCTIONS
# ======================================================================================================================

class PyPDF2:
  """
  PyPDF2 utility functions for link extraction

  """

  @staticmethod
  def get_annot_urls(fp: str, regex: UrlRegex) -> Set[str]:
    """
    Extract Annotated URLs from PDF

    :param fp: Path to PDF
    :param regex: configuration to use
    :return: Set of URLs of PDF
    """
    from PyPDF2.pdf import PdfFileReader, PageObject
    urls = set()
    with open(fp, "rb") as file:
      pdf = PdfFileReader(file)
      for page in pdf.pages:
        page: PageObject = page.getObject()
        if '/Annots' in page.keys():
          for annot in page.get('/Annots'):
            annot = annot.getObject()
            if '/A' in annot.keys():
              annot_a = annot['/A'].getObject()
              if '/URI' in annot_a.keys():
                urls.add(Util.canonicalize_url(annot_a['/URI'], regex))
            if '/S' in annot.keys():
              annot_s = annot['/S'].getObject()
              if '/URI' in annot_s.keys():
                urls.add(Util.canonicalize_url(annot_s['/URI'], regex))
    return Util.get_valid_urls(urls, regex)


# ======================================================================================================================
# PDFMINER FUNCTIONS
# ======================================================================================================================

class PDFMiner:
  """
  PDFMiner utility functions for link extraction

  """

  @staticmethod
  def get_full_text(fp: str) -> str:
    """
    Extract Full Text from PDF

    :param fp: Path to PDF
    :return: Full Text of PDF
    """
    from pdfminer.high_level import extract_text
    with open(fp, "rb") as file:
      _content = extract_text(file)
    return str(_content)


# ======================================================================================================================
# GROBID FUNCTIONS
# ======================================================================================================================

class GROBID:
  """
  GROBID utility functions for link extraction

  """

  @staticmethod
  def get_tei_xml(fp: str) -> str:
    """
    Convert PDF to TEI-XML

    :param fp: Path to PDF
    :return: TEI-XML of PDF
    """
    from grobid_client.grobid_client import GrobidClient
    client = GrobidClient(config_path="./grobid-service/config/config.json")
    [_pdf_file, _status, _content] = client.process_pdf(
      service="processFulltextDocument",
      pdf_file=fp,
      generateIDs=False,
      consolidate_header=False,
      consolidate_citations=False,
      include_raw_citations=False,
      include_raw_affiliations=False,
      teiCoordinates=False
    )
    return str(_content)

  @staticmethod
  def get_annot_urls(tei_xml: str, regex: UrlRegex) -> Set[str]:
    """
    Extract Annotated URLs from TEI-XML

    :param tei_xml: TEI-XML string
    :param regex: configuration to use
    :return: Set of URLs of TEI-XML
    """
    matches = bs4.BeautifulSoup(tei_xml, 'lxml-xml').find_all('ptr', {'target': True})
    urls = set({Util.canonicalize_url(match['target'], regex) for match in matches})
    return Util.get_valid_urls(urls, regex)

  @staticmethod
  def get_full_text(tei_xml: str) -> str:
    """
    Extract Full Text from TEI-XML

    :param tei_xml: TEI-XML string
    :return: Full Text of TEI-XML
    """
    lines = bs4.BeautifulSoup(tei_xml, 'lxml-xml').find_all(text=True)
    return "\n".join(lines)


# ======================================================================================================================
# URL EXTRACTORS
# ======================================================================================================================


class Extractor:
  """
  Base extractor. Should be implemented as a subclass

  """

  def get_text(self, fp: str) -> str:
    raise NotImplementedError('Base Class!')

  @staticmethod
  def get_annot_urls(regex: UrlRegex, fp: str) -> List[str]:
    return sorted(PyPDF2.get_annot_urls(fp, regex))

  def get_text_urls(self, regex: UrlRegex, fp: str) -> List[str]:
    raise NotImplementedError('Base Class!')

  def get_all_urls(self, regex: UrlRegex, fp: str) -> List[str]:
    # extract annotated URLs (baseline, always valid)
    annot_urls = set(self.get_annot_urls(regex, fp))
    # extract full text URLs (error-prone)
    full_text_urls = set(self.get_text_urls(regex, fp))
    # pick unique URLs from full_text_urls
    full_text_urls = Util.pick_uniq_urls(full_text_urls)
    # pick URLs from full_text_urls do not match (exact/partial) any URL in annot_urls
    full_text_urls = Util.pick_new_urls(full_text_urls, annot_urls)
    # concatenate, sort, and return
    return sorted(annot_urls.union(full_text_urls))


class PDFMExtractor(Extractor):
  """
  URL extractor using PyPDF2 -> PDFMiner

  """

  def get_text(self, fp: str) -> str:
    return PDFMiner.get_full_text(fp)

  def get_text_urls(self, regex: UrlRegex, fp: str) -> List[str]:
    # extract full text from PDF
    full_text = self.get_text(fp)
    # extract full text URLs
    full_text_urls = Util.harvest_urls(full_text, regex)
    # pick unique URLs from full_text_urls
    full_text_urls = Util.pick_uniq_urls(full_text_urls)
    # sort and return
    return sorted(full_text_urls)


class GROBExtractor(Extractor):
  """
  URL extractor using PyPDF2 -> GROBID

  """

  def get_text(self, fp: str) -> str:
    return GROBID.get_tei_xml(fp)

  def get_text_urls(self, regex: UrlRegex, fp: str) -> List[str]:
    # convert PDF to TEI-XML
    tei_xml = self.get_text(fp)
    # extract annotated URLs from TEI-XML (assumed valid)
    tei_urls = GROBID.get_annot_urls(tei_xml, regex)
    # pick unique URLs from tei_urls
    tei_urls = Util.pick_uniq_urls(tei_urls)
    # extract full text from TEI-XML
    full_text = GROBID.get_full_text(tei_xml)
    # extract full text URLs
    full_text_urls = Util.harvest_urls(full_text, regex)
    # pick unique URLs from full_text_urls
    full_text_urls = Util.pick_uniq_urls(full_text_urls)
    # pick URLs from full_text_urls that do not match (exact/partial) any URL in tei_urls
    full_text_urls = Util.pick_new_urls(full_text_urls, tei_urls)
    # concatenate, sort, and return
    return sorted(tei_urls.union(full_text_urls))


# ======================================================================================================================
# MAIN EXECUTION
# ======================================================================================================================

if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Link Extractor')
  parser.add_argument('-e', required=True, help="extractor to use", choices=['PDFM', 'GROB'])
  parser.add_argument('-c', required=True, help="command to run", choices=['TXT', 'U_ANN', 'U_TXT', 'U_ALL'])
  parser.add_argument('-r', metavar='OPTION_NUMBER', required=False, help="regex option to use", type=int)
  parser.add_argument('-i', metavar='INPUT_FILE', required=True, help="path to input file", type=str)
  parser.add_argument('-o', metavar='OUTPUT_FILE', required=False, help="path to output file", type=str)
  args = parser.parse_args()

  # select extractor to use
  if args.e == 'PDFM':
    e = PDFMExtractor()
  elif args.e == 'GROB':
    e = GROBExtractor()
  else:
    raise NotImplementedError('Extractor Does Not Exist!')

  # execute command
  if args.c == 'TXT':
    result = e.get_text(args.i)
  elif args.c == 'U_ANN':
    result = "\n".join(e.get_annot_urls(UrlRegex(args.r), args.i))
  elif args.c == 'U_TXT':
    result = "\n".join(e.get_text_urls(UrlRegex(args.r), args.i))
  elif args.c == 'U_ALL':
    result = "\n".join(e.get_all_urls(UrlRegex(args.r), args.i))
  else:
    raise NotImplementedError('Command Does Not Exist!')

  # write output
  if args.o:
    with open(args.o, 'w') as f_out:
      f_out.write(result)
  else:
    print(result)
