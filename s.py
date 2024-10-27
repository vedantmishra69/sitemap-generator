import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import time
import os

class SitemapGenerator:
    def __init__(self, base_url):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.sitemap_urls = []
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; SitemapGenerator/1.0)'
        }

    def normalize_url(self, url):
        """Normalize URL by removing fragments and trailing slashes."""
        # Remove URL fragment
        url, _ = urldefrag(url)
        # Remove trailing slash if present
        if url.endswith('/'):
            url = url[:-1]
        return url

    def is_valid_url(self, url):
        """Check if URL belongs to the same domain and is valid."""
        parsed = urlparse(url)
        return (
            parsed.netloc == self.domain
            and parsed.scheme in ('http', 'https')
            and not url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip'))
        )

    def get_links_from_page(self, url):
        """Extract all links from a webpage."""
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = set()
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                absolute_url = urljoin(url, href)
                normalized_url = self.normalize_url(absolute_url)
                if self.is_valid_url(normalized_url):
                    links.add(normalized_url)
            
            return links
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            return set()

    def crawl(self, url, max_pages=500):
        """Crawl the website starting from the given URL."""
        if len(self.visited_urls) >= max_pages:
            return

        # Normalize the URL before processing
        normalized_url = self.normalize_url(url)
        
        if normalized_url in self.visited_urls:
            return

        print(f"Crawling: {normalized_url}")
        self.visited_urls.add(normalized_url)
        self.sitemap_urls.append({
            'loc': normalized_url,
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'priority': '0.8'
        })

        # Get all links from the current page
        links = self.get_links_from_page(normalized_url)
        
        # Crawl each link
        for link in links:
            if link not in self.visited_urls:
                time.sleep(1)  # Be nice to the server
                self.crawl(link, max_pages)

    def generate_xml(self, output_file='output/sitemap.xml'):
        """Generate XML sitemap file."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

        for url_info in self.sitemap_urls:
            url_element = ET.SubElement(urlset, 'url')
            
            loc = ET.SubElement(url_element, 'loc')
            loc.text = url_info['loc']
            
            lastmod = ET.SubElement(url_element, 'lastmod')
            lastmod.text = url_info['lastmod']
            
            priority = ET.SubElement(url_element, 'priority')
            priority.text = url_info['priority']

        xml_str = minidom.parseString(ET.tostring(urlset)).toprettyxml(indent="  ")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        print(f"Sitemap generated: {output_file}")

def main():
    # Get parameters from environment variables or use defaults
    website_url = os.getenv('WEBSITE_URL', 'https://example.com')
    max_pages = int(os.getenv('MAX_PAGES', '500'))
    
    print(f"Starting sitemap generation for: {website_url}")
    print(f"Maximum pages to crawl: {max_pages}")
    
    generator = SitemapGenerator(website_url)
    generator.crawl(website_url, max_pages)
    generator.generate_xml()

if __name__ == "__main__":
    main()