"""GitHub profile scraper."""
import re
from scrapers.base_scraper import BaseScraper


class GitHubScraper(BaseScraper):
    """Scraper for GitHub profiles."""
    
    def scrape(self, url):
        """
        Scrape GitHub profile for commits in last 12 months and public repos.
        
        Args:
            url: GitHub profile URL
            
        Returns:
            Tuple of (success, dict_with_commits_and_repos_or_error_message)
        """
        if not url:
            return False, "No URL provided"
        
        # Ensure we're on the profile page, not a specific repo
        if '/repos' in url or '/projects' in url:
            # Extract base profile URL
            match = re.match(r'(https?://github\.com/[^/]+)', url)
            if match:
                url = match.group(1)
        
        # Fetch the page
        success, content = self.fetch_page(url)
        if not success:
            return False, content
        
        try:
            soup = self.parse_html(content)
            if not soup:
                return False, "Failed to parse HTML"
            
            result = {
                'commits_12mo': 'N/A',
                'public_repos': 'N/A'
            }
            
        # Extract commits in last 12 months from contribution graph
            commits_12mo = self._extract_commits(soup)
            if commits_12mo is not None:
                result['commits_12mo'] = str(commits_12mo)
            else:
                # Try fetching contributions page directly (GitHub sometimes loads this via XHR/include-fragment)
                try:
                    username = url.rstrip('/').split('/')[-1]
                    contrib_url = f"https://github.com/users/{username}/contributions"
                    success_contrib, content_contrib = self.fetch_page(contrib_url)
                    if success_contrib:
                        soup_contrib = self.parse_html(content_contrib)
                        if soup_contrib:
                            commits = self._extract_commits_from_contrib_page(soup_contrib)
                            if commits:
                                result['commits_12mo'] = str(commits)
                except Exception as e:
                    print(f"Error fetching contributions: {e}")
            
            # Extract public repositories count
            public_repos = self._extract_public_repos(soup)
            if public_repos is not None:
                result['public_repos'] = str(public_repos)
            
            # Check if we got at least one metric
            if result['commits_12mo'] != 'N/A' or result['public_repos'] != 'N/A':
                return True, result
            else:
                return False, "Could not extract GitHub metrics"
        
        except Exception as e:
            return False, f"Parsing error: {str(e)}"
    
    def _extract_commits(self, soup):
        """
        Extract total commits in last 12 months from contribution calendar.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Number of commits or None
        """
        try:
            # Method 1: Look for contribution summary text
            # GitHub shows "X contributions in the last year"
            contrib_text = soup.find('h2', class_='f4 text-normal mb-2')
            if contrib_text:
                text = contrib_text.get_text()
                match = re.search(r'([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year', text)
                if match:
                    commits = match.group(1).replace(',', '')
                    return int(commits)
            
            # Method 2: Look in the contribution graph area
            contrib_area = soup.find('div', class_=re.compile(r'js-yearly-contributions'))
            if contrib_area:
                # Look for the summary text
                summary = contrib_area.find('h2')
                if summary:
                    text = summary.get_text()
                    match = re.search(r'([\d,]+)\s+contributions?', text)
                    if match:
                        commits = match.group(1).replace(',', '')
                        return int(commits)
            
            # Method 3: Sum up contributions from SVG calendar
            # GitHub uses SVG rects with data-count attributes
            svg = soup.find('svg', class_=re.compile(r'js-calendar-graph-svg'))
            if svg:
                rects = svg.find_all('rect', {'data-count': True})
                if rects:
                    total = sum(int(rect.get('data-count', 0)) for rect in rects)
                    return total
            
            # Method 4: Look for any text mentioning contributions
            page_text = soup.get_text()
            match = re.search(r'([\d,]+)\s+contributions?\s+in\s+(?:the\s+)?last\s+year', page_text, re.IGNORECASE)
            if match:
                commits = match.group(1).replace(',', '')
                return int(commits)
            
            return None
        
        except Exception:
            return None
    
    def _extract_public_repos(self, soup):
        """
        Extract number of public repositories.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Number of public repos or None
        """
        try:
            # Method 1: Look for repository counter in navigation
            # GitHub shows "Repositories X" in the profile nav
            repo_link = soup.find('a', href=re.compile(r'\?tab=repositories'))
            if repo_link:
                # Look for counter span
                counter = repo_link.find('span', class_='Counter')
                if counter:
                    text = counter.get_text().strip()
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        repos = match.group(1).replace(',', '')
                        return int(repos)
            
            # Method 2: Look for any element with repository count
            counters = soup.find_all('span', class_='Counter')
            for counter in counters:
                # Check if this counter is near "repositories" text
                parent = counter.parent
                if parent and 'repositor' in parent.get_text().lower():
                    text = counter.get_text().strip()
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        repos = match.group(1).replace(',', '')
                        return int(repos)
            
            
            # Method 3: Look in navigation items
            nav_items = soup.find_all(['a', 'span'], text=re.compile(r'repositor', re.IGNORECASE))
            for item in nav_items:
                text = item.get_text()
                match = re.search(r'([\d,]+)', text)
                if match:
                    repos = match.group(1).replace(',', '')
                    return int(repos)
            
            return None
        
        except Exception:
            return None

    def _extract_commits_from_contrib_page(self, soup):
        """
        Extract commits from contributions page (e.g. /users/username/contributions).
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Number of commits or None
        """
        try:
            # Look for h2 with contribution count
            headers = soup.find_all('h2')
            for h2 in headers:
                text = h2.get_text()
                match = re.search(r'([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year', text, re.IGNORECASE | re.DOTALL)
                if match:
                    return int(match.group(1).replace(',', ''))
            return None
        except Exception:
            return None
