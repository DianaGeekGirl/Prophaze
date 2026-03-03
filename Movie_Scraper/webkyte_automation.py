import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime


class WebkyteMovieSearch:
    """Automated movie search tool for demo.webkyte.com"""
    
    def __init__(self, headless: bool = False, timeout: int = 30000):
        """
        Initialize the WebkyteMovieSearch automation tool
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Default timeout for operations in milliseconds
        """
        self.url = "https://demo.webkyte.com/"
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup_browser(self):
        """Initialize browser and context"""
        try:
            print(f"[{self._timestamp()}] Launching browser...")
            self.playwright = await async_playwright().start()
            
            # Launch browser with anti-detection settings
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            # Create context with realistic viewport
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create new page
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            
            print(f"[{self._timestamp()}] Browser launched successfully!")
            return True
            
        except Exception as e:
            print(f"[{self._timestamp()}] ERROR: Failed to setup browser - {str(e)}")
            return False
    
    async def navigate_to_site(self):
        """Navigate to the demo website"""
        try:
            print(f"[{self._timestamp()}] Navigating to {self.url}...")
            await self.page.goto(self.url, wait_until='networkidle')
            print(f"[{self._timestamp()}] Successfully loaded the website!")
            return True
            
        except PlaywrightTimeoutError:
            print(f"[{self._timestamp()}] ERROR: Timeout while loading the website")
            return False
        except Exception as e:
            print(f"[{self._timestamp()}] ERROR: Failed to navigate - {str(e)}")
            return False
    
    async def search_movie(self, movie_name: str):
        """
        Search for a movie and click the first suggestion
        
        Args:
            movie_name (str): Name of the movie to search
        """
        try:
            print(f"[{self._timestamp()}] Searching for movie: '{movie_name}'")
            
            # Wait for search input to be visible
            print(f"[{self._timestamp()}] Waiting for search input...")
            search_input = await self.page.wait_for_selector(
                'input[type="text"], input[placeholder*="search" i], input[name*="search" i]',
                timeout=10000
            )
            
            if not search_input:
                # Try alternative selectors
                search_input = await self.page.query_selector('input')
            
            # Clear and enter movie name
            print(f"[{self._timestamp()}] Entering movie name...")
            await search_input.click()
            await search_input.fill('')  # Clear existing text
            await search_input.type(movie_name, delay=100)  # Type with human-like delay
            
            # Wait a moment for suggestions to appear
            await asyncio.sleep(2)
            
            # Click on first suggestion using provided XPath
            print(f"[{self._timestamp()}] Waiting for suggestions to appear...")
            first_suggestion = await self.page.wait_for_selector(
                "xpath=//div[@class='sc-kUouGy fZpYWg']//div[@class='sc-eqNDNG hSZWzL'][1]",
                timeout=10000
            )
            
            if first_suggestion:
                print(f"[{self._timestamp()}] Clicking on first suggestion...")
                await first_suggestion.click()
                
                # Wait for navigation or content update
                await asyncio.sleep(2)
                
                print(f"[{self._timestamp()}] ✓ Successfully clicked first suggestion!")
                
                # Get current URL for verification
                current_url = self.page.url
                print(f"[{self._timestamp()}] Current URL: {current_url}")
                
                return True
            else:
                print(f"[{self._timestamp()}] ERROR: No suggestions found")
                return False
                
        except PlaywrightTimeoutError:
            print(f"[{self._timestamp()}] ERROR: Timeout - Element not found")
            return False
        except Exception as e:
            print(f"[{self._timestamp()}] ERROR: Search failed - {str(e)}")
            return False
    
    async def click_detect_copies(self):
        """Click the DETECT COPIES button"""
        try:
            print(f"[{self._timestamp()}] Waiting for 'DETECT COPIES' button...")
            detect_button = await self.page.wait_for_selector(
                "xpath=//button[text()='DETECT COPIES']",
                timeout=10000
            )
            
            if detect_button:
                print(f"[{self._timestamp()}] Clicking 'DETECT COPIES' button...")
                await detect_button.click()
                print(f"[{self._timestamp()}] ✓ Button clicked successfully!")
                return True
            else:
                print(f"[{self._timestamp()}] ERROR: DETECT COPIES button not found")
                return False
                
        except PlaywrightTimeoutError:
            print(f"[{self._timestamp()}] ERROR: Timeout - DETECT COPIES button not found")
            return False
        except Exception as e:
            print(f"[{self._timestamp()}] ERROR: Failed to click button - {str(e)}")
            return False
    
    async def collect_links(self):
        """Collect links from Telegram and Online platforms"""
        try:
            print(f"[{self._timestamp()}] Waiting for results sections to load...")
            
            # Wait for at least one result section to appear and be visible
            await self.page.wait_for_selector(
                "xpath=//div[@class='sc-eZSpzM eLoTJi']",
                state='visible',
                timeout=60000
            )
            
            print(f"[{self._timestamp()}] Results sections appeared!")
            
            # Wait for "Search in progress" to disappear
            print(f"[{self._timestamp()}] Waiting for search to complete...")
            try:
                await self.page.wait_for_selector(
                    "xpath=//*[contains(text(), 'Search in progress')]",
                    state='hidden',
                    timeout=120000
                )
                print(f"[{self._timestamp()}] Search completed!")
            except PlaywrightTimeoutError:
                print(f"[{self._timestamp()}] Warning: Timeout waiting for search completion, proceeding anyway...")
            
            print(f"[{self._timestamp()}] Waiting additional 5 seconds...")
            await asyncio.sleep(5)
            
            results = {
                'telegram': [],
                'online_platforms': []
            }
            
            # Collect Telegram links with pagination
            print(f"\n[{self._timestamp()}] === Collecting Telegram Links ===")
            try:
                telegram_pagination = await self.page.query_selector(
                    'xpath=(//div[@class="sc-zOxLx jpOOwO"])[1]'
                )
                
                if telegram_pagination:
                    # Get all page numbers (both active and inactive)
                    all_pages = await telegram_pagination.query_selector_all(
                        'xpath=.//span[@class="sc-jxYSNo gekosy"] | .//span[@class="sc-jxYSNo lkeBAZ"]'
                    )
                    
                    total_pages = len(all_pages)
                    print(f"[{self._timestamp()}] Found {total_pages} pages for Telegram")
                    
                    for page_num in range(1, total_pages + 1):
                        print(f"[{self._timestamp()}] Processing Telegram page {page_num}/{total_pages}...")
                        
                        # Click on the page number
                        page_span = await telegram_pagination.query_selector(
                            f'xpath=.//span[text()="{page_num}"]'
                        )
                        
                        if page_span:
                            await page_span.click()
                            await asyncio.sleep(3)
                            
                            # Collect links on this page
                            telegram_rows = await self.page.query_selector_all(
                                'xpath=//div[@class="sc-ctAsvE bjRUDb"]//div[@data-table-row="data"]'
                            )
                            
                            page_collected = 0
                            for row in telegram_rows:
                                # Get row text and split by columns
                                row_text = await row.inner_text()
                                # Split by newlines or tabs
                                row_data = [cell.strip() for cell in row_text.split('\n') if cell.strip()]
                                
                                if row_data:
                                    # Check if this exact row already exists
                                    row_exists = False
                                    for existing_row in results['telegram']:
                                        if existing_row == row_data:
                                            row_exists = True
                                            break
                                    
                                    if not row_exists:
                                        results['telegram'].append(row_data)
                                        page_collected += 1
                            
                            print(f"[{self._timestamp()}] Page {page_num}: Collected {page_collected} new rows (Total: {len(results['telegram'])})")
                        else:
                            print(f"[{self._timestamp()}] Could not find page {page_num} span")
                else:
                    print(f"[{self._timestamp()}] No Telegram pagination found, collecting current page only...")
                    telegram_rows = await self.page.query_selector_all(
                        'xpath=//div[@class="sc-ctAsvE bjRUDb"]//div[@data-table-row="data"]'
                    )
                    
                    for row in telegram_rows:
                        row_text = await row.inner_text()
                        row_data = [cell.strip() for cell in row_text.split('\n') if cell.strip()]
                        if row_data:
                            results['telegram'].append(row_data)
                
                print(f"[{self._timestamp()}] Total Telegram rows collected: {len(results['telegram'])}")
                    
            except Exception as e:
                print(f"[{self._timestamp()}] Error collecting Telegram links: {str(e)}")
            
            # Collect Online Platform links with pagination
            print(f"\n[{self._timestamp()}] === Collecting Online Platform Links ===")
            try:
                online_pagination = await self.page.query_selector(
                    'xpath=(//div[@class="sc-zOxLx jpOOwO"])[2]'
                )
                
                if online_pagination:
                    # Get all page numbers (both active and inactive)
                    all_pages = await online_pagination.query_selector_all(
                        'xpath=.//span[@class="sc-jxYSNo gekosy"] | .//span[@class="sc-jxYSNo lkeBAZ"]'
                    )
                    
                    total_pages = len(all_pages)
                    print(f"[{self._timestamp()}] Found {total_pages} pages for Online Platforms")
                    
                    for page_num in range(1, total_pages + 1):
                        print(f"[{self._timestamp()}] Processing Online Platform page {page_num}/{total_pages}...")
                        
                        # Click on the page number
                        page_span = await online_pagination.query_selector(
                            f'xpath=.//span[text()="{page_num}"]'
                        )
                        
                        if page_span:
                            await page_span.click()
                            await asyncio.sleep(3)
                            
                            # Collect links on this page
                            online_rows = await self.page.query_selector_all(
                                'xpath=//div[@class="sc-ctAsvE fSVrgT"]//div[@data-table-row="data"]'
                            )
                            
                            page_collected = 0
                            for row in online_rows:
                                # Get row text and split by columns
                                row_text = await row.inner_text()
                                # Split by newlines or tabs
                                row_data = [cell.strip() for cell in row_text.split('\n') if cell.strip()]
                                
                                if row_data:
                                    # Check if this exact row already exists
                                    row_exists = False
                                    for existing_row in results['online_platforms']:
                                        if existing_row == row_data:
                                            row_exists = True
                                            break
                                    
                                    if not row_exists:
                                        results['online_platforms'].append(row_data)
                                        page_collected += 1
                            
                            print(f"[{self._timestamp()}] Page {page_num}: Collected {page_collected} new rows (Total: {len(results['online_platforms'])})")
                        else:
                            print(f"[{self._timestamp()}] Could not find page {page_num} span")
                else:
                    print(f"[{self._timestamp()}] No Online Platform pagination found, collecting current page only...")
                    online_rows = await self.page.query_selector_all(
                        'xpath=//div[@class="sc-ctAsvE fSVrgT"]//div[@data-table-row="data"]'
                    )
                    
                    for row in online_rows:
                        row_text = await row.inner_text()
                        row_data = [cell.strip() for cell in row_text.split('\n') if cell.strip()]
                        if row_data:
                            results['online_platforms'].append(row_data)
                
                print(f"[{self._timestamp()}] Total Online Platform rows collected: {len(results['online_platforms'])}")
                    
            except Exception as e:
                print(f"[{self._timestamp()}] Error collecting Online Platform links: {str(e)}")
            
            # IMPORTANT: Wait for statistics to be fully rendered after all data is collected
            print(f"\n[{self._timestamp()}] Waiting for statistics to fully render...")
            await asyncio.sleep(3)
            
            # Extract statistics from the page AFTER data collection
            print(f"\n[{self._timestamp()}] === Extracting Statistics ===")
            try:
                stats = await self.extract_statistics()
                if stats:
                    results['statistics'] = stats
                    print(f"[{self._timestamp()}] Statistics extracted successfully:")
                    print(f"  - Telegram Results: {stats.get('telegram_results', 'N/A')}")
                    print(f"  - Telegram Views: {stats.get('telegram_views', 'N/A')}")
                    print(f"  - Online Results: {stats.get('online_results', 'N/A')}")
                    print(f"  - Online Views: {stats.get('online_views', 'N/A')}")
                else:
                    print(f"[{self._timestamp()}] Warning: Could not extract statistics")
                    results['statistics'] = None
            except Exception as e:
                print(f"[{self._timestamp()}] Error extracting statistics: {str(e)}")
                results['statistics'] = None
            
            return results
            
        except PlaywrightTimeoutError:
            print(f"[{self._timestamp()}] ERROR: Timeout waiting for results sections to load")
            return None
        except Exception as e:
            print(f"[{self._timestamp()}] ERROR: Failed to collect links - {str(e)}")
            return None
    
    async def extract_statistics(self):
        """
        Extract statistics (COPIES and VIEWS) from the demo.webkyte.com page.
        Uses multiple strategies for robustness against styled-components CSS class changes.

        Expected order: Telegram Results, Telegram Views, Online Results, Online Views

        Returns:
            dict: Statistics with telegram_results, telegram_views, online_results, online_views
        """
        try:
            stats = {}

            # Strategy 1: Original class-based selector
            print(f"[{self._timestamp()}] Strategy 1: Trying class-based selector...")
            xpath_base = '//span[@class="sc-hWgKua bbCQUw"]'

            try:
                await self.page.wait_for_selector(
                    f'xpath={xpath_base}',
                    state='visible',
                    timeout=5000
                )
            except Exception:
                pass  # Will try alternative strategies

            stat_elements = await self.page.query_selector_all(f'xpath={xpath_base}')
            print(f"[{self._timestamp()}] Class selector found {len(stat_elements)} elements")

            if len(stat_elements) >= 4:
                stats['telegram_results'] = await stat_elements[0].inner_text()
                stats['telegram_views'] = await stat_elements[1].inner_text()
                stats['online_results'] = await stat_elements[2].inner_text()
                stats['online_views'] = await stat_elements[3].inner_text()
                print(f"[{self._timestamp()}] Strategy 1 succeeded!")
                self._log_stats(stats)
                return stats

            # Strategy 2: JavaScript - find stat spans by font-size grouping
            # Stat values are displayed prominently (large font) and contain only numbers
            # They are NOT inside table rows or pagination
            print(f"[{self._timestamp()}] Strategy 2: Trying JS font-size grouping...")

            js_stats = await self.page.evaluate('''() => {
                const numericSpans = [];

                document.querySelectorAll('span').forEach(span => {
                    // Skip spans inside table data rows or pagination
                    if (span.closest('[data-table-row]')) return;

                    const text = span.innerText.trim();
                    // Match numbers with possible spaces/commas (e.g., "50", "28 237", "1,234")
                    if (!/^\\d[\\d\\s,]*$/.test(text)) return;

                    const rect = span.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) return;

                    const style = window.getComputedStyle(span);
                    const fontSize = parseFloat(style.fontSize);

                    // Stat values are typically 16px+ (larger than table text)
                    if (fontSize < 14) return;

                    numericSpans.push({
                        text: text,
                        top: rect.top,
                        left: rect.left,
                        fontSize: fontSize,
                        className: span.className
                    });
                });

                if (numericSpans.length === 0) {
                    return { error: 'No numeric spans found' };
                }

                // Group spans by font size
                const sizeGroups = {};
                numericSpans.forEach(s => {
                    const key = Math.round(s.fontSize);
                    if (!sizeGroups[key]) sizeGroups[key] = [];
                    sizeGroups[key].push(s);
                });

                // Find a group with exactly 4 elements (our 4 stat values)
                // Prefer larger font sizes
                let statGroup = null;
                const sortedSizes = Object.keys(sizeGroups)
                    .map(Number)
                    .sort((a, b) => b - a);

                for (const size of sortedSizes) {
                    if (sizeGroups[size].length === 4 && size >= 16) {
                        statGroup = sizeGroups[size];
                        break;
                    }
                }

                // Fallback: largest font group with at least 4 elements
                if (!statGroup) {
                    for (const size of sortedSizes) {
                        if (sizeGroups[size].length >= 4 && size >= 16) {
                            // Sort by position and take first 4
                            sizeGroups[size].sort((a, b) => {
                                if (Math.abs(a.top - b.top) < 30) return a.left - b.left;
                                return a.top - b.top;
                            });
                            statGroup = sizeGroups[size].slice(0, 4);
                            break;
                        }
                    }
                }

                if (statGroup) {
                    // Sort by position (top to bottom, left to right)
                    statGroup.sort((a, b) => {
                        if (Math.abs(a.top - b.top) < 30) return a.left - b.left;
                        return a.top - b.top;
                    });

                    return {
                        telegram_results: statGroup[0].text,
                        telegram_views: statGroup[1].text,
                        online_results: statGroup[2].text,
                        online_views: statGroup[3].text,
                        _method: 'font_size_grouping',
                        _class: statGroup[0].className
                    };
                }

                // Debug info
                return {
                    error: 'Could not identify stat group',
                    debug: numericSpans.slice(0, 20).map(s => ({
                        text: s.text, fontSize: s.fontSize,
                        top: Math.round(s.top), left: Math.round(s.left),
                        className: s.className
                    }))
                };
            }''')

            if js_stats and js_stats.get('telegram_results'):
                print(f"[{self._timestamp()}] Strategy 2 succeeded (method: {js_stats.get('_method')})")
                if js_stats.get('_class'):
                    print(f"[{self._timestamp()}] TIP: Update xpath class to '{js_stats['_class']}' for faster extraction")
                stats = {
                    'telegram_results': js_stats['telegram_results'],
                    'telegram_views': js_stats['telegram_views'],
                    'online_results': js_stats['online_results'],
                    'online_views': js_stats['online_views']
                }
                self._log_stats(stats)
                return stats

            if js_stats and js_stats.get('debug'):
                print(f"[{self._timestamp()}] Strategy 2 debug - numeric spans found:")
                for item in js_stats['debug']:
                    print(f"  text='{item['text']}', fontSize={item['fontSize']}, top={item['top']}, class='{item['className']}'")
            if js_stats and js_stats.get('error'):
                print(f"[{self._timestamp()}] Strategy 2 error: {js_stats['error']}")

            # Strategy 3: Text-based extraction from page content
            print(f"[{self._timestamp()}] Strategy 3: Trying text-based extraction...")

            page_text = await self.page.evaluate('() => document.body.innerText')
            print(f"[{self._timestamp()}] Page text (first 2000 chars):\n{page_text[:2000]}")

            import re
            # Look for patterns like "NUMBER Results" and "NUMBER Views"
            results_matches = re.findall(r'([\d][\d\s,]*)\s*Results?', page_text, re.IGNORECASE)
            views_matches = re.findall(r'([\d][\d\s,]*)\s*Views?', page_text, re.IGNORECASE)

            if len(results_matches) >= 2 and len(views_matches) >= 2:
                stats = {
                    'telegram_results': results_matches[0].strip(),
                    'telegram_views': views_matches[0].strip(),
                    'online_results': results_matches[1].strip(),
                    'online_views': views_matches[1].strip()
                }
                print(f"[{self._timestamp()}] Strategy 3 succeeded!")
                self._log_stats(stats)
                return stats

            # Save debug screenshot
            try:
                from pathlib import Path
                debug_dir = Path(__file__).parent / "results"
                debug_dir.mkdir(exist_ok=True)
                screenshot_path = debug_dir / f"debug_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"[{self._timestamp()}] Debug screenshot saved: {screenshot_path}")
            except Exception as ss_err:
                print(f"[{self._timestamp()}] Could not save debug screenshot: {ss_err}")

            print(f"[{self._timestamp()}] All strategies failed to extract statistics")
            return None

        except Exception as e:
            print(f"[{self._timestamp()}] Error extracting statistics: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _log_stats(self, stats):
        """Log extracted statistics"""
        print(f"[{self._timestamp()}] Extracted statistics:")
        print(f"  Telegram Results (COPIES): '{stats.get('telegram_results', 'N/A')}'")
        print(f"  Telegram Views: '{stats.get('telegram_views', 'N/A')}'")
        print(f"  Online Results (COPIES): '{stats.get('online_results', 'N/A')}'")
        print(f"  Online Views: '{stats.get('online_views', 'N/A')}'")
    
    async def cleanup(self):
        """Close browser and cleanup resources"""
        try:
            print(f"[{self._timestamp()}] Cleaning up resources...")
            
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                
            print(f"[{self._timestamp()}] Cleanup completed!")
            
        except Exception as e:
            print(f"[{self._timestamp()}] WARNING: Error during cleanup - {str(e)}")
    
    @staticmethod
    def _timestamp():
        """Generate timestamp for logging"""
        return datetime.now().strftime('%H:%M:%S')