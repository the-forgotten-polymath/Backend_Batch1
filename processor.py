"""Excel processing and enrichment logic."""
import os
import time
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from config import Config
from utils.validators import sanitize_url, validate_platform_url, normalize_column_name, extract_username_from_url
from utils.rate_limiter import RateLimiterManager
from scrapers import LeetCodeScraper, CodeforcesScraper, GitHubScraper, LinkedInScraper


class ProfileEnricher:
    """Process and enrich Excel file with profile data."""
    
    def __init__(self):
        """Initialize profile enricher."""
        self.rate_limiter = RateLimiterManager({
            'leetcode': Config.LEETCODE_RATE_LIMIT,
            'codeforces': Config.CODEFORCES_RATE_LIMIT,
            'linkedin': Config.LINKEDIN_RATE_LIMIT,
            'github': Config.GITHUB_RATE_LIMIT
        })
        
        self.scrapers = {
            'leetcode': LeetCodeScraper(),
            'codeforces': CodeforcesScraper(),
            'github': GitHubScraper(),
            'linkedin': LinkedInScraper()
        }
        
        self.logs = []
        self.stats = {
            'leetcode': {'success': 0, 'error': 0, 'errors': []},
            'codeforces': {'success': 0, 'error': 0, 'errors': []},
            'github': {'success': 0, 'error': 0, 'errors': []},
            'linkedin': {'success': 0, 'error': 0, 'errors': []}
        }
        
        self.start_time = None
        self.total_rows = 0
    
    def process_file(self, input_path, output_path):
        """Process Excel file and enrich with profile data."""
        self.start_time = time.time()
        
        try:
            df = pd.read_excel(input_path)
            self.total_rows = len(df)
            
            valid, error = self._validate_columns(df)
            if not valid:
                return False, error
            
            column_mapping = self._create_column_mapping(df)
            
            for col in Config.NEW_COLUMNS:
                df[col] = 'N/A'
            
            for idx, row in df.iterrows():
                self._process_row(idx, row, df, column_mapping)
            
            self._save_enriched_file(df, output_path)
            
            return True, None
        
        except Exception as e:
            return False, f"Processing error: {str(e)}"
    
    def _validate_columns(self, df):
        """Validate that required columns exist."""
        normalized_cols = [normalize_column_name(col) for col in df.columns]
        
        has_rollno = 'rollno' in normalized_cols
        has_url = any(col in normalized_cols for col in ['leetcodeurl', 'codeforcesurl', 'linkedinurl', 'githuburl'])
        
        if not has_rollno and not has_url:
            return False, "Excel must contain RollNo or at least one URL column"
        
        return True, None
    
    def _create_column_mapping(self, df):
        """Create mapping from normalized column names to actual column names."""
        mapping = {}
        for col in df.columns:
            normalized = normalize_column_name(col)
            mapping[normalized] = col
        return mapping
    
    def _get_column_value(self, row, column_mapping, normalized_name):
        """Get value from row using normalized column name."""
        if normalized_name in column_mapping:
            actual_col = column_mapping[normalized_name]
            value = row[actual_col]
            if pd.notna(value):
                return str(value).strip()
        return None
    
    def _process_row(self, idx, row, df, column_mapping):
        """Process a single row and enrich with profile data."""
        row_id = idx + 2
        
        roll_no = self._get_column_value(row, column_mapping, 'rollno')
        
        if not roll_no:
            github_url = self._get_column_value(row, column_mapping, 'githuburl')
            linkedin_url = self._get_column_value(row, column_mapping, 'linkedinurl')
            
            if github_url:
                roll_no = extract_username_from_url(github_url, 'github')
            elif linkedin_url:
                roll_no = extract_username_from_url(linkedin_url, 'linkedin')
            
            if not roll_no:
                roll_no = f"row_{row_id}"
        
        leetcode_url = self._get_column_value(row, column_mapping, 'leetcodeurl')
        if leetcode_url:
            leetcode_url = sanitize_url(leetcode_url)
            if leetcode_url and validate_platform_url(leetcode_url, 'leetcode'):
                self._process_leetcode(row_id, leetcode_url, df, idx)
        
        codeforces_url = self._get_column_value(row, column_mapping, 'codeforcesurl')
        if codeforces_url:
            codeforces_url = sanitize_url(codeforces_url)
            if codeforces_url and validate_platform_url(codeforces_url, 'codeforces'):
                self._process_codeforces(row_id, codeforces_url, df, idx)
        
        github_url = self._get_column_value(row, column_mapping, 'githuburl')
        if github_url:
            github_url = sanitize_url(github_url)
            if github_url and validate_platform_url(github_url, 'github'):
                self._process_github(row_id, github_url, df, idx)
        
        linkedin_url = self._get_column_value(row, column_mapping, 'linkedinurl')
        if linkedin_url:
            linkedin_url = sanitize_url(linkedin_url)
            if linkedin_url and validate_platform_url(linkedin_url, 'linkedin'):
                self._process_linkedin(row_id, linkedin_url, roll_no, df, idx)
    
    def _process_leetcode(self, row_id, url, df, idx):
        """Process LeetCode profile."""
        self.rate_limiter.wait_for_platform('leetcode')
        
        success, result = self.scrapers['leetcode'].scrape(url)
        
        timestamp = datetime.now().isoformat()
        if success:
            df.at[idx, 'LC_Global_Contest_Rank'] = result
            self.stats['leetcode']['success'] += 1
            self._add_log(timestamp, row_id, 'LeetCode', url, 'success', f'Rank: {result}')
        else:
            df.at[idx, 'LC_Global_Contest_Rank'] = 'N/A'
            self.stats['leetcode']['error'] += 1
            self.stats['leetcode']['errors'].append({'row': row_id, 'url': url, 'error': result})
            self._add_log(timestamp, row_id, 'LeetCode', url, 'error', result)
    
    def _process_codeforces(self, row_id, url, df, idx):
        """Process Codeforces profile."""
        self.rate_limiter.wait_for_platform('codeforces')
        
        success, result = self.scrapers['codeforces'].scrape(url)
        
        timestamp = datetime.now().isoformat()
        if success:
            df.at[idx, 'CF_Rating'] = result
            self.stats['codeforces']['success'] += 1
            self._add_log(timestamp, row_id, 'Codeforces', url, 'success', f'Rating: {result}')
        else:
            df.at[idx, 'CF_Rating'] = 'N/A'
            self.stats['codeforces']['error'] += 1
            self.stats['codeforces']['errors'].append({'row': row_id, 'url': url, 'error': result})
            self._add_log(timestamp, row_id, 'Codeforces', url, 'error', result)
    
    def _process_github(self, row_id, url, df, idx):
        """Process GitHub profile."""
        self.rate_limiter.wait_for_platform('github')
        
        success, result = self.scrapers['github'].scrape(url)
        
        timestamp = datetime.now().isoformat()
        if success:
            df.at[idx, 'GH_Commits_12mo'] = result['commits_12mo']
            df.at[idx, 'GH_Public_Repos'] = result['public_repos']
            self.stats['github']['success'] += 1
            self._add_log(timestamp, row_id, 'GitHub', url, 'success', 
                         f"Commits: {result['commits_12mo']}, Repos: {result['public_repos']}")
        else:
            df.at[idx, 'GH_Commits_12mo'] = 'N/A'
            df.at[idx, 'GH_Public_Repos'] = 'N/A'
            self.stats['github']['error'] += 1
            self.stats['github']['errors'].append({'row': row_id, 'url': url, 'error': result})
            self._add_log(timestamp, row_id, 'GitHub', url, 'error', result)
    
    def _process_linkedin(self, row_id, url, roll_no, df, idx):
        """Process LinkedIn profile."""
        self.rate_limiter.wait_for_platform('linkedin')
        
        success, result = self.scrapers['linkedin'].scrape(url, roll_no)
        
        timestamp = datetime.now().isoformat()
        if success:
            df.at[idx, 'Photos_Path'] = result
            self.stats['linkedin']['success'] += 1
            self._add_log(timestamp, row_id, 'LinkedIn', url, 'success', f'Photo: {result}')
        else:
            df.at[idx, 'Photos_Path'] = 'N/A'
            self.stats['linkedin']['error'] += 1
            self.stats['linkedin']['errors'].append({'row': row_id, 'url': url, 'error': result})
            self._add_log(timestamp, row_id, 'LinkedIn', url, 'error', result)
    
    def _add_log(self, timestamp, row_id, platform, url, status, message):
        """Add log entry."""
        self.logs.append({
            'timestamp': timestamp,
            'row_id': row_id,
            'platform': platform,
            'url': url,
            'status': status,
            'message': message
        })
    
    def _save_enriched_file(self, df, output_path):
        """Save enriched DataFrame to Excel with logs sheet."""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Enriched_Data', index=False)
            
            if self.logs:
                logs_df = pd.DataFrame(self.logs)
                logs_df.to_excel(writer, sheet_name='Enrich_Logs', index=False)
    
    def get_summary(self):
        """Get processing summary."""
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        summary = {
            'total_rows': self.total_rows,
            'total_duration_ms': duration_ms,
            'platforms': {}
        }
        
        for platform, stats in self.stats.items():
            total = stats['success'] + stats['error']
            success_rate = (stats['success'] / total * 100) if total > 0 else 0
            
            sample_errors = stats['errors'][:5]
            
            summary['platforms'][platform] = {
                'success_count': stats['success'],
                'error_count': stats['error'],
                'success_rate': round(success_rate, 2),
                'sample_errors': sample_errors
            }
        
        return summary
