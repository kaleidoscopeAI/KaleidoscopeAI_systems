import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self, base_url, max_depth=1):
        self.base_url = base_url
        self.max_depth = max_depth
        self.visited = set()
        self.data = []

    def crawl(self, url=None, depth=0):
        if url is None:
            url = self.base_url
        if depth > self.max_depth or url in self.visited:
            return
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            self.visited.add(url)
            soup = BeautifulSoup(response.content, "html.parser")
            chem_data = self._extract_chemical_data(soup)
            if chem_data:
                chem_data["url"] = url
                self.data.append(chem_data)
            else:
                title = soup.title.string if soup.title else "NoTitle"
                self.data.append({"title": title, "url": url})
            link_count = 0
            for link in soup.find_all("a", href=True):
                if link_count >= 10:
                    break
                next_url = urljoin(url, link["href"])
                if self._should_follow(next_url):
                    link_count += 1
                    self.crawl(next_url, depth + 1)
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")

    def _should_follow(self, url):
        return url.startswith(self.base_url)

    def _extract_chemical_data(self, soup):
        data = {}
        if "pubchem.ncbi.nlm.nih.gov" in self.base_url:
            data["smiles"] = self._find_pubchem_smiles(soup)
            data["iupac"] = self._find_pubchem_iupac(soup)
        elif "smiles" in self.base_url:
            data["smiles"] = self._extract_smiles_string(soup)
        if data.get("smiles"):
            return data
        return None

    def _find_pubchem_smiles(self, soup):
        tag = soup.find("meta", attrs={"name": "pubchem_smiles"})
        return tag["content"] if tag else None

    def _find_pubchem_iupac(self, soup):
        tag = soup.find("meta", attrs={"name": "pubchem_iupac"})
        return tag["content"] if tag else None

    def _extract_smiles_string(self, soup):
        pre = soup.find("pre", class_="smiles-data")
        return pre.text.strip() if pre else None

    def get_data(self):
        return self.data
