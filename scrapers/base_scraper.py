"""Base scraper class with retry logic and error handling."""
import time
import requests
from bs4 import BeautifulSoup
from config import Config


class BaseScraper:
    """Base class for all platform scrapers."""
    
    def __init__(self):
        """Initialize base scraper."""
        self.timeout = Config.REQUEST_TIMEOUT
        self.max_retries = Config.MAX_RETRIES
        self.backoff_factor = Config.RETRY_BACKOFF_FACTOR
        self.headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def fetch_page(self, url, retry_count=0):
        """
        Fetch page content with retry logic.
        
        Args:
            url: URL to fetch
            retry_count: Current retry attempt
            
        Returns:
            Tuple of (success, content_or_error_message)
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return True, response.text
            elif response.status_code == 404:
                return False, "Profile not found (404)"
            elif response.status_code == 403:
                return False, "Access forbidden (403)"
            elif response.status_code == 429:
                if retry_count < self.max_retries:
                    wait_time = self.backoff_factor ** (retry_count + 1)
                    time.sleep(wait_time)
                    return self.fetch_page(url, retry_count + 1)
                return False, "Rate limited (429)"
            else:
                return False, f"HTTP {response.status_code}"
        
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                time.sleep(self.backoff_factor ** retry_count)
                return self.fetch_page(url, retry_count + 1)
            return False, "Request timeout"
        
        except requests.exceptions.ConnectionError:
            if retry_count < self.max_retries:
                time.sleep(self.backoff_factor ** retry_count)
                return self.fetch_page(url, retry_count + 1)
            return False, "Connection error"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def parse_html(self, html_content):
        """
        Parse HTML content with BeautifulSoup.
        
        Args:
            html_content: HTML string
            
        Returns:
            BeautifulSoup object or None
        """
        try:
            return BeautifulSoup(html_content, 'lxml')
        except Exception:
            try:
                return BeautifulSoup(html_content, 'html.parser')
            except Exception:
                return None
    
    def scrape(self, url):
        """
        Main scraping method to be implemented by subclasses.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (success, data_or_error_message)
        """
        raise NotImplementedError("Subclasses must implement scrape method")
