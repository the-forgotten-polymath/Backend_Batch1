"""LinkedIn profile scraper."""
import os
import re
import requests
from PIL import Image
from io import BytesIO
from scrapers.base_scraper import BaseScraper
from config import Config


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn profiles."""
    
    def __init__(self):
        """Initialize LinkedIn scraper."""
        super().__init__()
        self.use_selenium = Config.SELENIUM_ENABLED
    
    def scrape(self, url, roll_no):
        """
        Scrape LinkedIn profile photo and save it.
        
        Args:
            url: LinkedIn profile URL
            roll_no: Student roll number for filename
            
        Returns:
            Tuple of (success, photo_path_or_error_message)
        """
        if not url:
            return False, "No URL provided"
        
        if not roll_no:
            return False, "No roll number provided for photo filename"
        
        # Try Selenium if enabled, otherwise use requests
        if self.use_selenium:
            return self._scrape_with_selenium(url, roll_no)
        else:
            return self._scrape_with_requests(url, roll_no)
    
    def _scrape_with_requests(self, url, roll_no):
        """
        Scrape LinkedIn photo using requests (limited, may not work due to auth).
        
        Args:
            url: LinkedIn profile URL
            roll_no: Student roll number
            
        Returns:
            Tuple of (success, photo_path_or_error_message)
        """
        # Fetch the page
        success, content = self.fetch_page(url)
        if not success:
            return False, content
        
        try:
            soup = self.parse_html(content)
            if not soup:
                return False, "Failed to parse HTML"
            
            # LinkedIn often requires authentication
            # Try to find profile image in meta tags (public profiles)
            img_url = None
            
            # Method 1: Look for og:image meta tag
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                img_url = og_image.get('content')
            
            # Method 2: Look for profile image in img tags
            if not img_url:
                profile_imgs = soup.find_all('img', class_=re.compile(r'profile|avatar|photo', re.IGNORECASE))
                for img in profile_imgs:
                    src = img.get('src') or img.get('data-src')
                    if src and ('profile' in src or 'photo' in src):
                        img_url = src
                        break
            
            if not img_url:
                return False, "Profile photo not found (may require authentication)"
            
            # Download and save the image
            return self._download_and_save_image(img_url, roll_no)
        
        except Exception as e:
            return False, f"Parsing error: {str(e)}"
    
    def _scrape_with_selenium(self, url, roll_no):
        """
        Scrape LinkedIn photo using Selenium for dynamic content.
        
        Args:
            url: LinkedIn profile URL
            roll_no: Student roll number
            
        Returns:
            Tuple of (success, photo_path_or_error_message)
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Setup Chrome options
            chrome_options = Options()
            if Config.SELENIUM_HEADLESS:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument(f'user-agent={Config.USER_AGENT}')
            
            # Initialize driver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            try:
                driver.get(url)
                
                # Wait for profile image to load
                wait = WebDriverWait(driver, 10)
                
                # Try different selectors for profile image
                selectors = [
                    "img.pv-top-card-profile-picture__image",
                    "img[class*='profile-photo']",
                    "img[class*='avatar']",
                    "img[alt*='profile']"
                ]
                
                img_element = None
                for selector in selectors:
                    try:
                        img_element = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if img_element:
                            break
                    except:
                        continue
                
                if not img_element:
                    driver.quit()
                    return False, "Profile photo element not found"
                
                img_url = img_element.get_attribute('src')
                if not img_url:
                    driver.quit()
                    return False, "Profile photo URL not found"
                
                driver.quit()
                
                # Download and save the image
                return self._download_and_save_image(img_url, roll_no)
            
            except Exception as e:
                driver.quit()
                return False, f"Selenium error: {str(e)}"
        
        except ImportError:
            return False, "Selenium not properly installed"
        except Exception as e:
            return False, f"Selenium setup error: {str(e)}"
    
    def _download_and_save_image(self, img_url, roll_no):
        """
        Download image from URL and save to photos folder.
        
        Args:
            img_url: Image URL
            roll_no: Student roll number
            
        Returns:
            Tuple of (success, photo_path_or_error_message)
        """
        try:
            # Create photos directory if it doesn't exist
            os.makedirs(Config.PHOTOS_FOLDER, exist_ok=True)
            
            # Download image
            response = requests.get(img_url, headers=self.headers, timeout=self.timeout)
            if response.status_code != 200:
                return False, f"Failed to download image (HTTP {response.status_code})"
            
            # Open and save image with Pillow
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Save as JPEG
            filename = f"{roll_no}.jpg"
            filepath = os.path.join(Config.PHOTOS_FOLDER, filename)
            img.save(filepath, 'JPEG', quality=85)
            
            # Return relative path
            relative_path = f"photos/{filename}"
            return True, relative_path
        
        except Exception as e:
            return False, f"Image save error: {str(e)}"
