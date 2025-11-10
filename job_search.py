import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote, urlencode
import logging

logger = logging.getLogger(__name__)

class JobSearch:
    def __init__(self, search_keywords: List[str], locations: List[str]):
        self.search_keywords = search_keywords
        self.locations = locations
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_drushim(self, keyword: str, location: str = "Israel") -> List[Dict]:
        """Search jobs on Drushim (Israeli job site)"""
        jobs = []
        try:
            # Map keywords to Drushim category IDs
            category_map = {
                'devops engineer': '491',
                'devops': '491',
                'devsecops': '491',  # DevSecOps is also in DevOps category
                'sre': '491',  # SRE is also in DevOps category
                'cloud engineer': '491',
                'cloud': '491'
            }
            
            # Normalize keyword for category lookup
            keyword_lower = keyword.lower().strip()
            # Handle variations of keywords
            if 'devsecops' in keyword_lower or 'dev sec ops' in keyword_lower:
                keyword_lower = 'devsecops'
            elif 'devops' in keyword_lower:
                keyword_lower = 'devops'
            elif 'sre' in keyword_lower:
                keyword_lower = 'sre'
            elif 'cloud' in keyword_lower:
                keyword_lower = 'cloud'
            
            category_id = category_map.get(keyword_lower, '491')  # Default to DevOps category
            
            # Map experience level to Drushim experience parameter
            # Drushim experience parameters:
            # 0 = לא נדרש ניסיון (no experience required)
            # 1 = עד שנה (up to 1 year)
            # 2 = 1-2 שנים (1-2 years)
            # 3 = 3-5 שנים (3-5 years) - Too high for us
            # We want 0-3 years, so we'll search for experience=1 (0-1 year) and experience=2 (1-2 years)
            # This covers 0-3 years range better
            
            # Build Drushim URL using the exact format from the user's example
            # URL: https://www.drushim.co.il/jobs/subcat/491/?experience=2&searchterm=DevOps&ssaen=3
            # Map keywords to proper Drushim search terms
            keyword_normalized = keyword.lower().strip()
            search_term_map = {
                'devops engineer': 'DevOps',
                'devops': 'DevOps',
                'devsecops': 'DevSecOps',
                'sre': 'SRE',
                'cloud engineer': 'Cloud',
                'cloud': 'Cloud'
            }
            
            # Get the search term, defaulting to capitalized keyword if not in map
            search_term = search_term_map.get(keyword_normalized, keyword.replace(' ', '').capitalize())
            
            # Use experience=2 which filters for 1-2 years (closest to our 0-3 years requirement)
            # We'll also filter by experience in the job_filter module
            search_url = f"https://www.drushim.co.il/jobs/subcat/{category_id}/?experience=2&searchterm={search_term}&ssaen=3"
            logger.info(f"Searching Drushim for '{keyword}' (search term: '{search_term}') using URL: {search_url}")
            
            try:
                response = requests.get(search_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Parse jobs from the list page
                    # Drushim uses /job/{job_id}/{hash}/ format (singular "job", not "jobs")
                    # Examples: /job/35010030/7fce2efe/, /job/35164538/59724395/
                    job_links = soup.find_all('a', href=re.compile(r'/job/\d+/\w+/'))
                    logger.info(f"Found {len(job_links)} job links on Drushim page using /job/ pattern")
                    
                    if len(job_links) == 0:
                        # Fallback: try without the hash part
                        job_links = soup.find_all('a', href=re.compile(r'/job/\d+'))
                        logger.info(f"Found {len(job_links)} job links with fallback pattern")
                        
                        if len(job_links) == 0:
                            logger.warning(f"WARNING: No job links found on Drushim page. URL: {search_url}")
                            # Check if page has job content
                            page_text = soup.get_text()
                            if 'דרושים' in page_text or 'משרות' in page_text or 'לפני' in page_text:
                                logger.warning("Page contains job-related content, but job links not found")
                    
                    # Process each job link
                    # Note: We'll fetch each job page to get details (slower but more reliable)
                    seen_urls = set()
                    processed_count = 0
                    max_jobs = 20  # Increased limit for better coverage
                    logger.info(f"Processing up to {max_jobs} jobs from {len(job_links)} links found")
                    for link in job_links:
                        if processed_count >= max_jobs:
                            logger.info(f"Reached max_jobs limit ({max_jobs}), stopping processing")
                            break
                        try:
                            # Get job URL
                            href = link.get('href', '')
                            if not href:
                                continue
                            
                            # Drushim job URLs are in format /job/{id}/{hash}/
                            # Make sure it's a valid job URL (not a category or search page)
                            if not re.search(r'/job/\d+', href):
                                continue
                            
                            if not href.startswith('http'):
                                job_url = f"https://www.drushim.co.il{href}"
                            else:
                                job_url = href
                            
                            # Skip duplicates
                            if job_url in seen_urls:
                                continue
                            seen_urls.add(job_url)
                            processed_count += 1
                            logger.debug(f"Processing job {processed_count}/{max_jobs}: {job_url}")
                            
                            # Get the parent container to extract job details
                            parent = link.find_parent(['article', 'div', 'li', 'tr', 'td'])
                            if not parent:
                                parent = link.find_parent()
                            
                            # Extract job title
                            # The link we found is just an "open in new window" icon
                            # We need to fetch the actual job page to get the title
                            title = ''
                            job_page_response = None
                            job_soup = None
                            
                            try:
                                # Fetch the job page to get the title
                                job_page_response = requests.get(job_url, headers=self.headers, timeout=10)
                                if job_page_response.status_code == 200:
                                    job_soup = BeautifulSoup(job_page_response.content, 'html.parser')
                                    
                                    # Look for title in various places on the job page
                                    # Method 1: Look for h1 or h2 with title/job classes
                                    title_elem = job_soup.find(['h1', 'h2'], class_=re.compile(r'title|job|position|name', re.I))
                                    if title_elem:
                                        title = title_elem.get_text(strip=True)
                                    
                                    # Method 2: Look for any h1 (usually the job title)
                                    if not title or len(title) < 3:
                                        h1 = job_soup.find('h1')
                                        if h1:
                                            title = h1.get_text(strip=True)
                                    
                                    # Method 3: Look for page title tag
                                    if not title or len(title) < 3:
                                        if job_soup.title:
                                            title_text = job_soup.title.get_text(strip=True)
                                            # Remove site name if present
                                            title = title_text.split('|')[0].split('-')[0].strip()
                                    
                                    # Method 4: Look for meta title
                                    if not title or len(title) < 3:
                                        meta_title = job_soup.find('meta', property='og:title')
                                        if meta_title:
                                            title = meta_title.get('content', '').strip()
                                
                                if not title or len(title) < 3:
                                    logger.warning(f"Could not extract title from job page {job_url[:80]}")
                                    continue
                                    
                            except Exception as e:
                                logger.error(f"Error fetching job page {job_url[:80]}: {e}", exc_info=True)
                                continue
                            
                            # Extract company name and description from job page
                            company = ''
                            description = ''
                            
                            # Use the job page soup we already fetched
                            if job_page_response and job_page_response.status_code == 200 and job_soup:
                                # Extract company from job page
                                company_elem = job_soup.find(['span', 'div', 'a'], class_=re.compile(r'company|employer|חברה', re.I))
                                if company_elem:
                                    company = company_elem.get_text(strip=True)
                                
                                # Extract description from job page
                                desc_elem = job_soup.find(['div', 'section'], class_=re.compile(r'description|תיאור|details', re.I))
                                if desc_elem:
                                    description = desc_elem.get_text(strip=True)[:500]
                                else:
                                    # Get all paragraphs
                                    paragraphs = job_soup.find_all('p')
                                    if paragraphs:
                                        description = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])[:500]
                            
                            # Fallback to parent if job page didn't have info
                            if not company and parent:
                                # Try multiple ways to find company
                                company_text = parent.get_text()
                                # Look for company name patterns
                                company_match = re.search(r'([A-Z][a-zA-Z\s&]+(?:Team|Technologies|Systems|Solutions|Ltd|Inc)?)', company_text)
                                if company_match:
                                    company = company_match.group(1).strip()
                                
                                # Also try to find in structured elements
                                if not company:
                                    company_elem = parent.find(['span', 'div', 'a'], class_=re.compile(r'company|employer', re.I))
                                    if company_elem:
                                        company = company_elem.get_text(strip=True)
                            
                            # Extract location from job page
                            location_text = location
                            if job_page_response and job_page_response.status_code == 200 and job_soup:
                                location_elem = job_soup.find(['span', 'div'], class_=re.compile(r'location|area|city|מיקום', re.I))
                                if location_elem:
                                    location_text = location_elem.get_text(strip=True)
                            
                            # Extract posted date from job page
                            parent_text = ''
                            if job_page_response and job_page_response.status_code == 200 and job_soup:
                                # Get all text from job page
                                parent_text = job_soup.get_text()
                            
                            # Also check sibling elements for date info
                            if parent:
                                # Look for time/date elements in the parent and its siblings
                                time_elems = parent.find_all(['time', 'span', 'div', 'p'], class_=re.compile(r'time|date|posted|לפני|שעות|דקות', re.I))
                                for time_elem in time_elems:
                                    time_text = time_elem.get_text()
                                    if re.search(r'לפני|היום|שעות|דקות|ימים', time_text, re.I):
                                        parent_text += ' ' + time_text
                                
                                # Also check parent's siblings for date info
                                if parent.parent:
                                    siblings = parent.parent.find_all(['span', 'div', 'time'], class_=re.compile(r'time|date|posted', re.I))
                                    for sibling in siblings:
                                        sibling_text = sibling.get_text()
                                        if re.search(r'לפני|היום|שעות|דקות|ימים', sibling_text, re.I):
                                            parent_text += ' ' + sibling_text
                                
                                # Check parent's parent for date info
                                grandparent = parent.find_parent()
                                if grandparent:
                                    grandparent_text = grandparent.get_text()
                                    # Check if grandparent has date info
                                    if re.search(r'לפני|היום|שעות|דקות|ימים|שבועות', grandparent_text, re.I):
                                        parent_text += ' ' + grandparent_text
                            
                            # Parse the date from the collected text
                            posted_date = self._parse_drushim_date(parent_text)
                            
                            # Debug: Log if we found date info
                            if posted_date:
                                hours_ago = (datetime.utcnow() - posted_date).total_seconds() / 3600
                                logger.info(f"Added job: {title[:50]} - Posted {hours_ago:.1f} hours ago (Date: {posted_date})")
                            else:
                                # Try to find date info in the full page text if not found in parent
                                if 'לפני' in parent_text or 'היום' in parent_text:
                                    logger.warning(f"Warning: Could not parse date for '{title[:50]}' but found date indicators in text")
                                else:
                                    logger.info(f"Added job: {title[:50]} - No date found in text (will be included if from today)")
                            
                            job = {
                                'title': title,
                                'company': company or 'Unknown',
                                'location': location_text,
                                'url': job_url,
                                'description': description or '',
                                'source': 'drushim',
                                'posted_date': posted_date
                            }
                            jobs.append(job)
                            logger.info(f"Successfully added job: '{title[:60]}' from {company or 'Unknown'}")
                        except Exception as e:
                            logger.error(f"Error parsing Drushim job: {e}", exc_info=True)
                            continue
                else:
                    logger.error(f"Failed to fetch Drushim page: {response.status_code}")
            except Exception as e:
                logger.error(f"Error fetching Drushim: {e}", exc_info=True)
                            
        except Exception as e:
            logger.error(f"Error in search_drushim: {e}", exc_info=True)
        
        logger.info(f"Returning {len(jobs)} jobs from Drushim for keyword '{keyword}'")
        return jobs
    
    def search_gotfriends(self, keyword: str, location: str = "Israel") -> List[Dict]:
        """Search jobs on GotFriends (Israeli job site)"""
        jobs = []
        try:
            # GotFriends uses category-based URLs
            category_urls = {
                'devops engineer': 'https://www.gotfriends.co.il/jobslobby/system/devops-positions/',
                'devops': 'https://www.gotfriends.co.il/jobslobby/system/devops-positions/',
                'devsecops': 'https://www.gotfriends.co.il/jobslobby/system/devops-positions/',  # DevSecOps in DevOps category
                'sre': 'https://www.gotfriends.co.il/jobslobby/system/sre/',
                'cloud engineer': 'https://www.gotfriends.co.il/jobslobby/system/devops-positions/',  # Cloud often in DevOps
                'cloud': 'https://www.gotfriends.co.il/jobslobby/system/devops-positions/'
            }
            
            # Normalize keyword for category lookup
            keyword_lower = keyword.lower().strip()
            # Handle variations
            if 'devsecops' in keyword_lower or 'dev sec ops' in keyword_lower:
                keyword_lower = 'devsecops'
            elif 'devops' in keyword_lower:
                keyword_lower = 'devops'
            elif 'sre' in keyword_lower:
                keyword_lower = 'sre'
            elif 'cloud' in keyword_lower:
                keyword_lower = 'cloud'
            
            # Get the appropriate URL for the keyword
            search_url = category_urls.get(keyword_lower, 'https://www.gotfriends.co.il/jobslobby/system/devops-positions/')
            logger.info(f"Searching GotFriends for '{keyword}' using URL: {search_url}")
            
            # Note: GotFriends may filter by experience on the page itself
            # We'll filter by experience in the job_filter after fetching
            
            response = requests.get(search_url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse GotFriends job listings
                # Look for job links on the page
                job_links = soup.find_all('a', href=re.compile(r'/job/|/position/|/jobs/'))
                logger.info(f"Found {len(job_links)} GotFriends job links")
                if len(job_links) == 0:
                    logger.warning(f"WARNING: No job links found on GotFriends page. URL: {search_url}")
                
                seen_urls = set()
                for link in job_links[:30]:  # Limit to 30 jobs
                    try:
                        # Get job URL
                        href = link.get('href', '')
                        if not href:
                            continue
                        
                        if not href.startswith('http'):
                            job_url = f"https://www.gotfriends.co.il{href}"
                        else:
                            job_url = href
                        
                        # Skip duplicates
                        if job_url in seen_urls:
                            continue
                        seen_urls.add(job_url)
                        
                        # Get parent container
                        parent = link.find_parent(['article', 'div', 'li', 'tr', 'td'])
                        if not parent:
                            parent = link.find_parent()
                        
                        # Extract job title
                        title = link.get_text(strip=True)
                        if not title or len(title) < 3:
                            title_elem = parent.find(['h2', 'h3', 'h4']) if parent else None
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                        
                        if not title or len(title) < 3:
                            continue
                        
                        # Extract company
                        company = ''
                        if parent:
                            company_text = parent.get_text()
                            company_match = re.search(r'([A-Z][a-zA-Z\s&]+(?:Team|Technologies|Systems|Solutions|Ltd|Inc)?)', company_text)
                            if company_match:
                                company = company_match.group(1).strip()
                            
                            if not company:
                                company_elem = parent.find(['span', 'div', 'a'], class_=re.compile(r'company|employer', re.I))
                                if company_elem:
                                    company = company_elem.get_text(strip=True)
                        
                        # Extract location
                        location_text = location
                        if parent:
                            location_elem = parent.find(['span', 'div'], class_=re.compile(r'location|area|city|מיקום', re.I))
                            if location_elem:
                                location_text = location_elem.get_text(strip=True)
                            else:
                                location_match = re.search(r'(תל\s*אביב|ירושלים|חיפה|רעננה|הרצליה|לוד|נתניה)', parent.get_text(), re.I)
                                if location_match:
                                    location_text = location_match.group(1)
                        
                        # Extract description
                        description = ''
                        if parent:
                            desc_elem = parent.find(['p', 'div'], class_=re.compile(r'description|summary|תיאור', re.I))
                            if desc_elem:
                                description = desc_elem.get_text(strip=True)[:300]
                            else:
                                para = parent.find('p')
                                if para:
                                    description = para.get_text(strip=True)[:300]
                        
                        # Extract posted date from GotFriends (similar pattern to Drushim)
                        parent_text = parent.get_text() if parent else ''
                        
                        # Check for date elements similar to Drushim
                        if parent:
                            # Look for time/date elements
                            time_elems = parent.find_all(['time', 'span', 'div', 'p'], class_=re.compile(r'time|date|posted|לפני|שעות|דקות', re.I))
                            for time_elem in time_elems:
                                time_text = time_elem.get_text()
                                if re.search(r'לפני|היום|שעות|דקות|ימים', time_text, re.I):
                                    parent_text += ' ' + time_text
                            
                            # Check parent's parent for date info
                            grandparent = parent.find_parent()
                            if grandparent:
                                grandparent_text = grandparent.get_text()
                                if re.search(r'לפני|היום|שעות|דקות|ימים|שבועות', grandparent_text, re.I):
                                    parent_text += ' ' + grandparent_text
                        
                        posted_date = self._parse_drushim_date(parent_text)
                        
                        # Debug: Log date info
                        if posted_date:
                            hours_ago = (datetime.utcnow() - posted_date).total_seconds() / 3600
                            logger.info(f"Added GotFriends job: {title[:50]} - Posted {hours_ago:.1f} hours ago")
                        else:
                            logger.info(f"Added GotFriends job: {title[:50]} - No date found")
                        
                        job = {
                            'title': title,
                            'company': company,
                            'location': location_text,
                            'url': job_url,
                            'description': description,
                            'source': 'gotfriends',
                            'posted_date': posted_date
                        }
                        jobs.append(job)
                    except Exception as e:
                        logger.error(f"Error parsing GotFriends job: {e}")
                        continue
            else:
                logger.error(f"Failed to fetch GotFriends page: {response.status_code}")
                            
        except Exception as e:
            logger.error(f"Error in search_gotfriends: {e}", exc_info=True)
        
        logger.info(f"Returning {len(jobs)} jobs from GotFriends for keyword '{keyword}'")
        return jobs
    
    def search_indeed_rss(self, keyword: str, location: str = "Israel") -> List[Dict]:
        """Search jobs using Indeed RSS feeds"""
        jobs = []
        try:
            # Indeed RSS feed format
            keyword_encoded = keyword.replace(' ', '+')
            location_encoded = location.replace(' ', '+').replace(',', '%2C')
            
            # Try different RSS URLs
            rss_urls = [
                f"https://www.indeed.com/rss?q={keyword_encoded}&l={location_encoded}&sort=date",
                f"https://rss.indeed.com/rss?q={keyword_encoded}&l={location_encoded}&sort=date"
            ]
            
            for rss_url in rss_urls:
                try:
                    feed = feedparser.parse(rss_url)
                    if feed.entries:
                        for entry in feed.entries:
                            job = {
                                'title': entry.get('title', ''),
                                'company': self._extract_company_from_title(entry.get('title', '')),
                                'location': location,
                                'url': entry.get('link', ''),
                                'description': entry.get('summary', ''),
                                'source': 'indeed',
                                'posted_date': self._parse_date(entry.get('published', ''))
                            }
                            jobs.append(job)
                        break  # If successful, no need to try other URLs
                except Exception as e:
                    print(f"Error fetching Indeed RSS from {rss_url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in search_indeed_rss: {e}")
        
        return jobs
    
    def search_serpapi(self, api_key: str, keyword: str, location: str = "Israel") -> List[Dict]:
        """Search jobs using SerpAPI (requires API key)"""
        if not api_key:
            logger.debug("SerpAPI key not provided, skipping SerpAPI search")
            return []
        
        jobs = []
        try:
            logger.info(f"Searching SerpAPI (Google Jobs) for '{keyword}' in '{location}'")
            params = {
                'engine': 'google_jobs',
                'q': keyword,
                'location': location,
                'api_key': api_key,
                'num': 20  # Number of results
            }
            
            response = requests.get('https://serpapi.com/search', params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'jobs_results' in data:
                logger.info(f"Found {len(data['jobs_results'])} jobs from SerpAPI for '{keyword}' in '{location}'")
                for job_result in data['jobs_results']:
                    job = {
                        'title': job_result.get('title', ''),
                        'company': job_result.get('company_name', ''),
                        'location': job_result.get('location', location),
                        'url': job_result.get('apply_options', [{}])[0].get('link', job_result.get('google_jobs_link', '')),
                        'description': job_result.get('description', ''),
                        'source': 'google_jobs',
                        'posted_date': self._parse_serpapi_date(job_result.get('detected_extensions', {}).get('posted_at'))
                    }
                    jobs.append(job)
            else:
                logger.info(f"No jobs found from SerpAPI for '{keyword}' in '{location}'")
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from SerpAPI for '{keyword}' in '{location}': {e}")
        except Exception as e:
            logger.error(f"Error in search_serpapi for '{keyword}' in '{location}': {e}", exc_info=True)
        
        logger.info(f"Returning {len(jobs)} jobs from SerpAPI for '{keyword}' in '{location}'")
        return jobs
    
    def search_job_aggregator(self, keyword: str) -> List[Dict]:
        """Search jobs from various aggregator sites using web scraping"""
        jobs = []
        
        # Note: This is a basic implementation. For production, consider using
        # proper scraping frameworks like Scrapy, or paid APIs like SerpAPI
        
        # Indeed web scraping (fallback if RSS doesn't work)
        try:
            keyword_encoded = keyword.replace(' ', '+')
            url = f"https://www.indeed.com/jobs?q={keyword_encoded}&sort=date&fromage=1"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                for card in job_cards[:10]:  # Limit to 10 results
                    try:
                        title_elem = card.find('h2', class_='jobTitle')
                        title = title_elem.get_text(strip=True) if title_elem else ''
                        job_link = title_elem.find('a') if title_elem else None
                        url_suffix = job_link.get('href', '') if job_link else ''
                        
                        company_elem = card.find('span', class_='companyName')
                        company = company_elem.get_text(strip=True) if company_elem else ''
                        
                        location_elem = card.find('div', class_='companyLocation')
                        location = location_elem.get_text(strip=True) if location_elem else ''
                        
                        snippet_elem = card.find('div', class_='job-snippet')
                        description = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                        if title and url_suffix:
                            full_url = f"https://www.indeed.com{url_suffix}" if url_suffix.startswith('/') else url_suffix
                            
                            job = {
                                'title': title,
                                'company': company,
                                'location': location,
                                'url': full_url,
                                'description': description,
                                'source': 'indeed_web',
                                'posted_date': datetime.utcnow()
                            }
                            jobs.append(job)
                    except Exception as e:
                        print(f"Error parsing job card: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error in search_job_aggregator: {e}")
        
        return jobs
    
    def search_all_sources(self, serpapi_key: Optional[str] = None) -> List[Dict]:
        """Search all available job sources"""
        all_jobs = []
        
        # Optimize: For Drushim and GotFriends, location doesn't affect the URL
        # So we only need to search once per unique search term, not per keyword×location
        # This reduces 20 searches (4 keywords × 5 locations) to just 4 searches
        
        # Get unique search terms for Drushim/GotFriends (they use the same category)
        unique_search_terms = set()
        for keyword in self.search_keywords:
            keyword_lower = keyword.lower().strip()
            if 'devsecops' in keyword_lower or 'dev sec ops' in keyword_lower:
                unique_search_terms.add('devsecops')
            elif 'devops' in keyword_lower:
                unique_search_terms.add('devops')
            elif 'sre' in keyword_lower:
                unique_search_terms.add('sre')
            elif 'cloud' in keyword_lower:
                unique_search_terms.add('cloud')
            else:
                unique_search_terms.add(keyword_lower)
        
        logger.info(f"Optimized search: Searching {len(unique_search_terms)} unique terms instead of {len(self.search_keywords) * len(self.locations)} keyword×location combinations")
        
        # Search Drushim once per unique search term
        for search_term in unique_search_terms:
            logger.info(f"Searching Drushim for '{search_term}'")
            drushim_jobs = self.search_drushim(search_term, "Israel")
            all_jobs.extend(drushim_jobs)
            time.sleep(1)  # Reduced delay since we're doing fewer searches
        
        # Search GotFriends once per unique search term
        for search_term in unique_search_terms:
            logger.info(f"Searching GotFriends for '{search_term}'")
            gotfriends_jobs = self.search_gotfriends(search_term, "Israel")
            all_jobs.extend(gotfriends_jobs)
            time.sleep(1)  # Reduced delay
        
        # For SerpAPI, we still search per keyword×location (if provided)
        # as it may have location-specific results
        if serpapi_key:
            logger.info(f"SerpAPI key provided - searching Google Jobs via SerpAPI")
            logger.info(f"This will perform {len(self.search_keywords) * len(self.locations)} SerpAPI searches ({len(self.search_keywords)} keywords × {len(self.locations)} locations)")
            for keyword in self.search_keywords:
                for location in self.locations:
                    serpapi_jobs = self.search_serpapi(serpapi_key, keyword, location)
                    all_jobs.extend(serpapi_jobs)
                    time.sleep(1)  # Delay to avoid rate limiting
        else:
            logger.info("SerpAPI key not provided - skipping Google Jobs search (add SERPAPI_KEY to .env to enable)")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.get('url') and job['url'] not in seen_urls:
                seen_urls.add(job['url'])
                unique_jobs.append(job)
        
        logger.info(f"Total unique jobs found: {len(unique_jobs)} (from {len(all_jobs)} total before deduplication)")
        return unique_jobs
    
    def _extract_company_from_title(self, title: str) -> str:
        """Extract company name from job title (format: "Job Title - Company Name")"""
        if ' - ' in title:
            return title.split(' - ')[-1].strip()
        return ''
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string from RSS feed"""
        try:
            # Try parsing common date formats
            from dateutil import parser
            return parser.parse(date_string)
        except:
            return datetime.utcnow()
    
    def _parse_drushim_date(self, text: str) -> Optional[datetime]:
        """Parse posted date from Drushim page text (e.g., 'לפני 3 שעות' = '3 hours ago', 'לפני מספר דקות' = 'a few minutes ago')"""
        try:
            if not text:
                return None
                
            # Patterns for Hebrew time expressions
            # לפני X שעות = X hours ago
            # לפני X דקות = X minutes ago
            # לפני מספר דקות = a few minutes ago (assume 5 minutes)
            # לפני מספר שעות = a few hours ago (assume 2 hours)
            # לפני X ימים = X days ago
            # לפני X שבועות = X weeks ago
            # Also check for date patterns like "02/11/2025"
            
            # Check for "מספר דקות" (a few minutes) - very recent
            few_minutes_pattern = r'לפני\s*מספר\s*דקות?'
            if re.search(few_minutes_pattern, text, re.IGNORECASE):
                # Assume "a few minutes" means 5 minutes ago
                return datetime.utcnow() - timedelta(minutes=5)
            
            # Check for "מספר שעות" (a few hours)
            few_hours_pattern = r'לפני\s*מספר\s*שעות?'
            if re.search(few_hours_pattern, text, re.IGNORECASE):
                # Assume "a few hours" means 2 hours ago
                return datetime.utcnow() - timedelta(hours=2)
            
            # Check for specific number of minutes ago
            minutes_pattern = r'לפני\s*(\d+)\s*דקות?'
            minutes_match = re.search(minutes_pattern, text, re.IGNORECASE)
            if minutes_match:
                minutes = int(minutes_match.group(1))
                # Accept any minutes (even if it's many, as long as it's reasonable)
                if minutes < 10080:  # 7 days * 24 hours * 60 minutes
                    return datetime.utcnow() - timedelta(minutes=minutes)
            
            # Check for specific number of hours ago (most common for recent jobs)
            hours_pattern = r'לפני\s*(\d+)\s*שעות?'
            hours_match = re.search(hours_pattern, text, re.IGNORECASE)
            if hours_match:
                hours = int(hours_match.group(1))
                # Accept hours up to 48 hours (to catch jobs from today even if posted early)
                if hours < 48:
                    return datetime.utcnow() - timedelta(hours=hours)
            
            # Check for "היום" (today) - explicitly today
            today_pattern = r'היום'
            if re.search(today_pattern, text, re.IGNORECASE):
                # If it says "today", return current time (or a few hours ago to be safe)
                return datetime.utcnow() - timedelta(hours=2)
            
            # Check for days ago
            days_pattern = r'לפני\s*(\d+)\s*ימים?'
            days_match = re.search(days_pattern, text, re.IGNORECASE)
            if days_match:
                days = int(days_match.group(1))
                if days == 0:
                    # "לפני 0 ימים" means today
                    return datetime.utcnow() - timedelta(hours=2)
                elif days <= 7:
                    return datetime.utcnow() - timedelta(days=days)
            
            # Check for weeks ago
            weeks_pattern = r'לפני\s*(\d+)\s*שבועות?'
            weeks_match = re.search(weeks_pattern, text, re.IGNORECASE)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                if weeks <= 2:
                    return datetime.utcnow() - timedelta(weeks=weeks)
            
            # If no pattern matches, return None
            # The filter will check if we should include it based on other criteria
            return None
        except Exception as e:
            logger.debug(f"Error parsing Drushim date from text '{text[:100]}': {e}")
            return None
    
    def _parse_serpapi_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Parse date from SerpAPI response"""
        if not date_string:
            return datetime.utcnow()
        return self._parse_date(date_string)

