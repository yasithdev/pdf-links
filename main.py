#!/usr/bin/env python3
import re
import time
from typing import Optional, List, Set

import bs4
# ======================================================================================================================
# REGEX CONFIGURATION
# ======================================================================================================================
import timeout_decorator


class UrlRegex:
  """
  Configuration class for URL regular expressions
  """

  @staticmethod
  def get_url_regex(option: int):

    __protocol = r"https?://"
    __port = r"(?::\d+)?"
    __tld = rf"({r'|'.join(Util.read_tld_list())})"

    # https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string
    if option in [1, 3]:
      # regex parts
      __host = rf"[\w\-]+(?:\.[\w\-]+)*\.{__tld}"
      __w3_host = rf"www(?:\.[\w\-]+)*\.{__tld}"
      __uchar = r"[\w.,@?^=%&:/~+#-]"
      __u_end = r"[\w?^%@&=~+#-]"
      __path = rf"(?:(?:{__uchar})+{__u_end})?"

      # configure host regex for partial URLs
      if option == 1:
        __p_host = __host
      elif option == 3:
        __p_host = __w3_host
      else:
        raise NotImplementedError('Option Does Not Exist!')

      return [
        re.compile(rf'({__protocol}{__host}{__port}{__path})', re.I),
        re.compile(rf'({__p_host}{__port}{__path})', re.I)
      ]

    # http://www.faqs.org/rfcs/rfc3986.html
    # https://webmasters.stackexchange.com/questions/90615/is-it-valid-to-include-digits-and-question-marks-in-the-url-slug-for-a-permalink/91211#91211
    elif option in [2, 4]:
      # regex parts
      __host = rf"[a-z\d\-]+(?:\.[a-z\d\-]+)*\.{__tld}"
      __w3_host = rf"www(?:\.[a-z\d\-]+)*\.{__tld}"
      __uchar = r"[\w:@\-.~!$&\'()*+,;=]|%[\da-f]{2}"
      __u_end = r"[\w^%@&=~+#-]"
      __path = rf"(?:(?:/(?:{__uchar})+{__u_end})+(?:/?\?(?:{__uchar})+{__u_end})?(?:/?#(?:{__uchar})+{__u_end})?)?"

      # configure host regex for partial URLs
      if option == 2:
        __p_host = __host
      elif option == 4:
        __p_host = __w3_host
      else:
        raise NotImplementedError('Option Does Not Exist!')

      return [
        re.compile(rf'({__protocol}{__host}{__port}{__path})', re.I),
        re.compile(rf'({__p_host}{__port}{__path})', re.I)
      ]
    else:
      raise NotImplementedError('Option Does Not Exist!')

  @staticmethod
  def get_blacklist_regex():
    return re.compile(rf".*({'|'.join(Util.read_blacklist())}).*", re.I)

  def __init__(self, option: int):
    # set regex URL patterns
    [self.FULL_URL, self.PARTIAL_URL] = self.get_url_regex(option)
    # set regex URL blacklist
    self.BLACKLIST = self.get_blacklist_regex()


# ======================================================================================================================
# UTILITY FUNCTIONS
# ======================================================================================================================

class Util:
  """
  Helper functions to perform link extraction from text

  """

  @staticmethod
  def read_blacklist(fp: str = 'resources/blacklist.txt') -> List[str]:
    with open(fp, 'r', encoding='utf-8') as f:
      return sorted(map(str.strip, f.readlines()))

  @staticmethod
  def read_tld_list(fp: str = 'resources/tld.txt') -> List[str]:
    with open(fp, 'r', encoding='utf-8') as f:
      return sorted(map(str.strip, f.readlines()), key=len, reverse=True)

  @staticmethod
  def canonicalize_url(url: str) -> Optional[str]:
    """
    Canonicalize a given URL.
    Returns None for malformed URLs

    :return: Canonical URL (or None)
    """
    # sanitize URL
    url = url.lower().strip(" /\n").replace(" ", "%20")
    # if full URL, return HTTPS/FTP URL
    if url.startswith("http://"):
      return f"https://{url[7:]}"
    elif url.startswith("https://"):
      return url
    else:
      return f"https://{url}"

  @staticmethod
  def get_valid_urls(s: Set[Optional[str]], online: bool = False) -> Set[str]:
    """
    Return the subset of valid URLs from a given set of URLs

    :param s: set of URLs to pick valid URLs from
    :param online: if True, send a HEAD request and check for 200 OK. Else (default) validate syntactically
    :return: subset of valid URLs
    """

    @timeout_decorator.timeout(seconds=2)
    def is_valid(url: str):
      # validate against URL blacklist
      if blacklist.search(url) is not None:
        return False
      # validate URL integrity
      if online:
        import requests
        return requests.head(url).ok
      else:
        import validators
        return validators.url(url, public=True)

    blacklist = UrlRegex.get_blacklist_regex()
    valid_urls = set()
    for u in s.difference({None}):
      try:
        if is_valid(u):
          valid_urls.add(u)
      except:
        continue
    return valid_urls

  @staticmethod
  def augment(text: str) -> str:
    # remove occurrences of [space(s)-newlines-space(s)]
    aug_text = re.sub(r"(\s*\n+\s*)", r"", text, flags=re.I)
    aug_text = re.sub(r"(https?://www\.|https?://|www\.)", r" \1", aug_text, flags=re.I)
    agg_text = f"{aug_text}\n{text}\n"
    return agg_text

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
    text = Util.augment(text)
    # parse and yield urls
    urls = set()

    def find_urls(v: str, r: re.Pattern) -> List[str]:
      for m in r.finditer(v):
        yield Util.canonicalize_url(m.group())

    urls = urls.union(find_urls(text, regex.FULL_URL))
    urls = urls.union(find_urls(text, regex.PARTIAL_URL))
    # get valid urls from the set
    valid_urls = Util.get_valid_urls(urls)
    return valid_urls

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
  def get_annot_urls(fp: str) -> Set[str]:
    """
    Extract Annotated URLs from PDF

    :param fp: Path to PDF
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
                urls.add(Util.canonicalize_url(annot_a['/URI']))
            if '/S' in annot.keys():
              annot_s = annot['/S'].getObject()
              if '/URI' in annot_s.keys():
                urls.add(Util.canonicalize_url(annot_s['/URI']))
    return Util.get_valid_urls(urls)


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
  def get_annot_urls(tei_xml: str) -> Set[str]:
    """
    Extract Annotated URLs from TEI-XML

    :param tei_xml: TEI-XML string
    :return: Set of URLs of TEI-XML
    """
    matches = bs4.BeautifulSoup(tei_xml, 'lxml-xml').find_all('ptr', {'target': True})
    urls = set({Util.canonicalize_url(match['target']) for match in matches})
    return Util.get_valid_urls(urls)

  @staticmethod
  def get_full_text(tei_xml: str) -> str:
    """
    Extract Full Text from TEI-XML

    :param tei_xml: TEI-XML string
    :return: Full Text of TEI-XML
    """
    lines = bs4.BeautifulSoup(tei_xml, 'lxml-xml').find_all(text=True)
    return "\n".join(lines)


class PDFIUM:
  """
PyPDFium utility functions for link extraction

"""

  @staticmethod
  def get_urls(fp: str) -> Set[str]:
    """
    Extract Annotated URLs from PDF

    :param fp: Path to PDF
    :return: Set of URLs of PDF
    """
    import pypdfium as pdfium
    import ctypes

    urls = set()
    buf_len = 2048
    buffer = (ctypes.c_ushort * buf_len)()
    buffer_ = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
    # this line is very important, otherwise it won't work
    pdfium.FPDF_InitLibraryWithConfig(pdfium.FPDF_LIBRARY_CONFIG(2, None, None, 0))

    doc = pdfium.FPDF_LoadDocument(fp, None)
    page_count = pdfium.FPDF_GetPageCount(doc)
    for i in range(page_count):
      # load PDF page
      page = pdfium.FPDF_LoadPage(doc, i)
      # load text in PDF page
      text = pdfium.FPDFText_LoadPage(page)
      # Load links in PDF text
      links = pdfium.FPDFLink_LoadWebLinks(text)
      link_count = pdfium.FPDFLink_CountWebLinks(links)
      # get each URL
      for j in range(link_count):
        url_length = pdfium.FPDFLink_GetURL(links, j, buffer_, buf_len)
        url_nums = buffer[:url_length - 1]
        url = ''.join(map(chr, url_nums))
        # ignore other protocols and mailto: links
        if url.startswith('http'):
          url = Util.canonicalize_url(url)
          urls.add(url)
      pdfium.FPDFLink_CloseWebLinks(links)
      pdfium.FPDFText_ClosePage(text)
      pdfium.FPDF_ClosePage(page)
    pdfium.FPDF_CloseDocument(doc)
    return Util.get_valid_urls(urls)


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
  def get_annot_urls(fp: str) -> List[str]:
    return sorted(PyPDF2.get_annot_urls(fp))

  def get_text_urls(self, fp: str, **kwargs) -> List[str]:
    raise NotImplementedError('Base Class!')

  def get_all_urls(self, fp: str, **kwargs) -> List[str]:
    # extract annotated URLs (baseline, always valid)
    annot_urls = set(self.get_annot_urls(fp))
    # extract full text URLs (error-prone)
    full_text_urls = set(self.get_text_urls(fp, **kwargs))
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

  def get_text_urls(self, fp: str, **kwargs) -> List[str]:
    regex: UrlRegex = kwargs['regex']
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

  def get_text_urls(self, fp: str, **kwargs) -> List[str]:
    regex: UrlRegex = kwargs['regex']
    # convert PDF to TEI-XML
    tei_xml = self.get_text(fp)
    # extract annotated URLs from TEI-XML (assumed valid)
    tei_urls = GROBID.get_annot_urls(tei_xml)
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


class PDFIUMExtractor(Extractor):
  """
  URL extractor using PyPDF2 -> PDFIUM

  """

  def get_text(self, fp: str) -> str:
    # TODO this is a fake full text extraction, as it only returns URLs for now
    return "\n".join(sorted(PDFIUM.get_urls(fp)))

  def get_text_urls(self, fp: str, **kwargs) -> List[str]:
    # extract full text from PDF
    # TODO this is a fake implementation, as it returns newline-concatenated URLs as full text
    full_text = self.get_text(fp)
    # extract full text URLs.
    full_text_urls = set(full_text.split("\n"))
    # pick unique URLs from full_text_urls
    full_text_urls = Util.pick_uniq_urls(full_text_urls)
    # sort and return
    return sorted(full_text_urls)


# ======================================================================================================================
# MAIN EXECUTION
# ======================================================================================================================

if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Link Extractor')
  parser.add_argument('-c', required=True, help="command to run", choices=['U_ANN', 'TXT', 'U_TXT', 'U_ALL'])
  parser.add_argument('-e', required=False, help="extractor to use", choices=['PDFM', 'PDFIUM', 'GROB'])
  parser.add_argument('-r', metavar='OPTION_NUMBER', required=False, help="regex option to use", type=int)
  parser.add_argument('-i', metavar='INPUT_FILE', required=True, help="path to input file", type=str)
  parser.add_argument('-o', metavar='OUTPUT_FILE', required=False, help="path to output file", type=str)
  args = parser.parse_args()

  # execute command
  if args.c == 'U_ANN':
    time_start = time.time_ns()
    result = "\n".join(sorted(PyPDF2.get_annot_urls(args.i)))
    time_end = time.time_ns()
  else:
    # select extractor to use
    if args.e == 'PDFM':
      e = PDFMExtractor()
    elif args.e == 'PDFIUM':
      e = PDFIUMExtractor()
    elif args.e == 'GROB':
      e = GROBExtractor()
    else:
      raise NotImplementedError('Extractor Does Not Exist!')
    # prepare kwargs
    kw = {}
    if args.r is not None:
      kw['regex'] = UrlRegex(args.r)
    # run extractor
    time_start = time.time_ns()
    if args.c == 'TXT':
      result = e.get_text(args.i)
    elif args.c == 'U_TXT':
      result = "\n".join(e.get_text_urls(args.i, **kw))
    elif args.c == 'U_ALL':
      result = "\n".join(e.get_all_urls(args.i, **kw))
    else:
      raise NotImplementedError('Command Does Not Exist!')
    time_end = time.time_ns()

  duration = (time_end - time_start) * 1e-9
  print(f'generated in {duration} seconds')

  # write output
  if args.o:
    with open(args.o, 'w') as f_out:
      f_out.write(result)
  else:
    print(result)
