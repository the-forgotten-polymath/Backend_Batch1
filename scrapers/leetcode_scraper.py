"""LeetCode profile scraper."""
import re
import json
from scrapers.base_scraper import BaseScraper


class LeetCodeScraper(BaseScraper):
    """Scraper for LeetCode profiles."""
    
    def scrape(self, url):
        """
        Scrape LeetCode profile for global contest rank.
        
        Args:
            url: LeetCode profile URL
            
        Returns:
            Tuple of (success, rank_or_error_message)
        """
        if not url:
            return False, "No URL provided"
        
        # Fetch the page
        success, content = self.fetch_page(url)
        if not success:
            return False, content
        
        try:
            # Try to find contest ranking in the page
            # LeetCode often embeds data in script tags or as JSON
            soup = self.parse_html(content)
            if not soup:
                return False, "Failed to parse HTML"
            
            # Method 1: Look for contest rank in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'ranking' in script.string.lower():
                    # Try to extract JSON data
                    try:
                        # Look for patterns like "ranking":12345
                        match = re.search(r'"ranking"\s*:\s*(\d+)', script.string)
                        if match:
                            rank = match.group(1)
                            return True, rank
                        
                        # Look for contestRanking
                        match = re.search(r'"contestRanking"\s*:\s*(\d+)', script.string)
                        if match:
                            rank = match.group(1)
                            return True, rank
                    except Exception:
                        continue
            
            # Method 2: Look for visible rank on the page
            # LeetCode shows contest rank in various places
            rank_patterns = [
                r'Contest\s+Rating[:\s]+(\d+)',
                r'Global\s+Ranking[:\s]+(\d+)',
                r'Ranking[:\s]+(\d+)',
            ]
            
            page_text = soup.get_text()
            for pattern in rank_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    rank = match.group(1)
                    return True, rank
            
            # Method 3: Look in specific divs/spans that might contain ranking
            rank_elements = soup.find_all(['div', 'span'], 
                                         text=re.compile(r'(ranking|rating)', re.IGNORECASE))
            for elem in rank_elements:
                # Look for numbers near ranking text
                parent_text = elem.parent.get_text() if elem.parent else ''
                match = re.search(r'\b(\d{1,7})\b', parent_text)
                if match:
                    rank = match.group(1)
                    # Sanity check: rank should be reasonable
                    if 1 <= int(rank) <= 10000000:
                        return True, rank
            
            return False, "Contest rank not found on profile"
        
        except Exception as e:
            return False, f"Parsing error: {str(e)}"
