#!/usr/bin/env python3
import re
from typing import Optional, List, Set, Type

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
      raise Exception('Requested Alternative Not Found')

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


class BaseExtractor:

  @staticmethod
  def get_urls(fp: str, regex: UrlRegex) -> List[str]:
    raise NotImplementedError('Base Class!')

  @staticmethod
  def get_text(fp: str) -> str:
    raise NotImplementedError('Base Class!')


class ExtractorA(BaseExtractor):
  """
  URL extraction using PyPDF2 -> PDFMiner

  """

  @staticmethod
  def get_urls(fp: str, regex: UrlRegex) -> List[str]:
    # step 1 - extract annotated URLs (baseline, assumed valid)
    annot_urls = PyPDF2.get_annot_urls(fp, regex)
    # step 2 - extract full text URLs (error-prone)
    full_text = PDFMiner.get_full_text(fp)
    full_text_urls = Util.harvest_urls(full_text, regex)
    # step 3 - get URLs in full_text_urls that do not match (exact/partial) any URL in annot_urls
    better_full_text_urls = annot_urls.copy()
    for url in full_text_urls:
      if not any(url == x or url[8:].find(x[8:]) != -1 or x[8:].find(url[8:]) != -1 for x in annot_urls):
        better_full_text_urls.add(url)
    # step 4 - concatenate urls, sort, and return
    final_urls = annot_urls.union(better_full_text_urls)
    return sorted(final_urls)

  @staticmethod
  def get_text(fp: str) -> str:
    return PDFMiner.get_full_text(fp)


class ExtractorB(BaseExtractor):
  """
  URL extraction using PyPDF2 -> GROBID

  """

  @staticmethod
  def get_urls(fp: str, regex: UrlRegex) -> List[str]:
    # step 1 - extract annotated URLs (baseline, assumed valid)
    annot_urls = PyPDF2.get_annot_urls(fp, regex)
    # step 2 - generate TEI-XML from PDF
    tei_xml = GROBID.get_tei_xml(fp)
    # step 3 - extract annotated URL from TEI-XML (error-prone)
    tei_urls = GROBID.get_annot_urls(tei_xml, regex)
    # step 4 - get URLs in tei_urls that do not match (exact/partial) any URL in annot_urls
    better_tei_urls = set()
    for url in tei_urls:
      if not any(url == x or url[8:].find(x[8:]) != -1 or x[8:].find(url[8:]) != -1 for x in annot_urls):
        better_tei_urls.add(url)
    # step 5 - extract full text URLs from TEI-XML (error-prone)
    full_text = GROBID.get_full_text(tei_xml)
    full_text_urls = Util.harvest_urls(full_text, regex)
    # step 6 - get URLs in full_text_urls that do not match (exact/partial) any URL in [annot_urls, better_tei_urls]
    better_full_text_urls = set()
    for url in full_text_urls:
      if not any(url == x or url[8:].find(x[8:]) != -1 or x[8:].find(url[8:]) != -1 for x in
                 annot_urls.union(better_tei_urls)):
        better_full_text_urls.add(url)
    # step 7 - concatenate urls, sort, and return
    final_urls = annot_urls.union(better_tei_urls).union(better_full_text_urls)
    return sorted(final_urls)

  @staticmethod
  def get_text(fp: str) -> str:
    return GROBID.get_tei_xml(fp)


# ======================================================================================================================
# MAIN EXECUTION
# ======================================================================================================================

if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Link Extractor')
  parser.add_argument('-e', required=True, help="extractor to use", choices=['A', 'B'])
  parser.add_argument('-c', required=True, help="command to execute", choices=['TXT', 'URL'])
  parser.add_argument('-r', required=False, help="regex config to use", type=int)
  parser.add_argument('-i', metavar='INPUT_PATH', required=True, help="path to input file")
  parser.add_argument('-o', metavar='OUTPUT_PATH', required=False, help="path to output file")
  args = parser.parse_args()

  # select extractor to use
  extractor: Type[BaseExtractor]
  if args.e == 'A':
    extractor = ExtractorA
  elif args.e == 'B':
    extractor = ExtractorB
  else:
    raise NotImplementedError('Requested Extractor Does Not Exist')

  # select command to execute
  if args.c == 'URL':
    fn = lambda x: '\n'.join(extractor.get_urls(x, UrlRegex(args.r)))
  elif args.c == 'TXT':
    fn = extractor.get_text
  else:
    raise NotImplementedError('Requested Method Does Not Exist')

  # execute command
  result = fn(args.i)
  if args.o:
    with open(args.o, 'w') as f_out:
      f_out.write(result)
  else:
    print(result)
