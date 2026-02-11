"""Codeforces profile scraper."""
import re
from scrapers.base_scraper import BaseScraper


class CodeforcesScraper(BaseScraper):
    """Scraper for Codeforces profiles."""
    
    def scrape(self, url):
        """
        Scrape Codeforces profile for current rating.
        
        Args:
            url: Codeforces profile URL
            
        Returns:
            Tuple of (success, rating_or_error_message)
        """
        if not url:
            return False, "No URL provided"
        
        # Fetch the page
        success, content = self.fetch_page(url)
        if not success:
            return False, content
        
        try:
            soup = self.parse_html(content)
            if not soup:
                return False, "Failed to parse HTML"
            
            # Method 1: Look for rating in user info
            # Codeforces shows rating in the user-rank span
            user_rank = soup.find('span', class_='user-rank')
            if user_rank:
                # Rating is often in a sibling or nearby element
                parent = user_rank.parent
                if parent:
                    # Look for rating pattern in parent text
                    text = parent.get_text()
                    match = re.search(r'\b(\d{3,4})\b', text)
                    if match:
                        rating = match.group(1)
                        return True, rating
            
            # Method 2: Look for rating in the main user info section
            info_divs = soup.find_all('div', class_='info')
            for div in info_divs:
                text = div.get_text()
                # Look for "Contest rating: 1234" or similar
                match = re.search(r'rating[:\s]+(\d{3,4})', text, re.IGNORECASE)
                if match:
                    rating = match.group(1)
                    return True, rating
            
            # Method 3: Look in user-info or profile-info sections
            user_info = soup.find('div', class_='user-info')
            if not user_info:
                user_info = soup.find('div', class_='main-info')
            
            if user_info:
                # Find all spans and divs that might contain rating
                for elem in user_info.find_all(['span', 'div', 'li']):
                    text = elem.get_text()
                    # Look for rating number (typically 3-4 digits)
                    if 'rating' in text.lower():
                        match = re.search(r'\b(\d{3,4})\b', text)
                        if match:
                            rating = match.group(1)
                            # Sanity check: rating typically between 0-4000
                            if 0 <= int(rating) <= 4000:
                                return True, rating
            
            # Method 4: Look for colored user rating (Codeforces uses colors)
            # Rating classes like user-blue, user-violet, etc.
            colored_user = soup.find('span', class_=re.compile(r'user-(red|orange|violet|blue|cyan|green|gray)'))
            if colored_user:
                # Rating might be in the same element or nearby
                text = colored_user.get_text()
                match = re.search(r'\b(\d{3,4})\b', text)
                if match:
                    rating = match.group(1)
                    return True, rating
                
                # Check siblings
                if colored_user.parent:
                    parent_text = colored_user.parent.get_text()
                    match = re.search(r'\b(\d{3,4})\b', parent_text)
                    if match:
                        rating = match.group(1)
                        return True, rating
            
            # Method 5: Look in the entire page for rating pattern
            page_text = soup.get_text()
            # Look for "Rating: 1234" or "Current rating: 1234"
            match = re.search(r'(?:current\s+)?rating[:\s]+(\d{3,4})', page_text, re.IGNORECASE)
            if match:
                rating = match.group(1)
                if 0 <= int(rating) <= 4000:
                    return True, rating
            
            return False, "Rating not found on profile"
        
        except Exception as e:
            return False, f"Parsing error: {str(e)}"
