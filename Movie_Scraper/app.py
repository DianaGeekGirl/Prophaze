from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import sys
import threading
import csv as csv_module

# Import the automation class
from webkyte_automation import WebkyteMovieSearch

app = Flask(__name__)
CORS(app)

# Directory for storing results - use absolute path
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

print(f"[INFO] Results directory: {RESULTS_DIR.absolute()}")

# Track active searches
active_searches = {}


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search_movie():
    """
    API endpoint to start a movie search
    Returns immediately with search_id, automation runs in background
    """
    try:
        data = request.get_json()
        movie_name = data.get('movie_name', '').strip()
        
        if not movie_name:
            return jsonify({
                'success': False,
                'error': 'Movie name is required'
            }), 400
        
        print(f"[API] Received search request for: {movie_name}")
        
        # Generate search ID and expected filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_movie_name = movie_name.replace(' ', '_')
        csv_filename = f"{safe_movie_name}_results_{timestamp}.csv"
        json_filename = f"{safe_movie_name}_results_{timestamp}.json"
        search_id = f"{safe_movie_name}_{timestamp}"
        
        # Track search status
        active_searches[search_id] = {
            'status': 'running',
            'movie_name': movie_name,
            'csv_filename': csv_filename,
            'json_filename': json_filename,
            'started_at': datetime.now().isoformat()
        }
        
        # Start automation in background thread
        thread = threading.Thread(
            target=run_automation_background,
            args=(movie_name, search_id, csv_filename, json_filename)
        )
        thread.daemon = True
        thread.start()
        
        # Return immediately
        return jsonify({
            'success': True,
            'search_id': search_id,
            'movie_name': movie_name,
            'csv_filename': csv_filename,
            'status': 'running',
            'message': 'Search started in background'
        }), 200
            
    except Exception as e:
        print(f"[API] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def run_automation_background(movie_name, search_id, csv_filename, json_filename):
    """Run automation in background thread"""
    try:
        # Run the async automation
        results = asyncio.run(run_automation(movie_name, csv_filename, json_filename))
        
        if results['success']:
            active_searches[search_id]['status'] = 'completed'
            active_searches[search_id]['completed_at'] = datetime.now().isoformat()
            active_searches[search_id]['results'] = results
            print(f"[BACKGROUND] Search {search_id} completed successfully")
        else:
            active_searches[search_id]['status'] = 'failed'
            active_searches[search_id]['error'] = results.get('error', 'Unknown error')
            print(f"[BACKGROUND] Search {search_id} failed: {results.get('error')}")
            
    except Exception as e:
        active_searches[search_id]['status'] = 'failed'
        active_searches[search_id]['error'] = str(e)
        print(f"[BACKGROUND] Search {search_id} error: {str(e)}")



@app.route('/api/download/<filename>')
def download_file(filename):
    """Download CSV file"""
    try:
        filepath = RESULTS_DIR / filename
        print(f"[DOWNLOAD] Looking for file: {filepath.absolute()}")
        
        if filepath.exists():
            print(f"[DOWNLOAD] File found! Sending: {filepath}")
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )
        else:
            # Check if file exists anywhere in results directory
            print(f"[DOWNLOAD] File not found at: {filepath.absolute()}")
            print(f"[DOWNLOAD] Files in results dir:")
            if RESULTS_DIR.exists():
                for f in RESULTS_DIR.iterdir():
                    print(f"  - {f.name}")
            else:
                print(f"[DOWNLOAD] Results directory doesn't exist: {RESULTS_DIR.absolute()}")
            
            return jsonify({
                'success': False,
                'error': f'File not found: {filename}'
            }), 404
    except Exception as e:
        print(f"[DOWNLOAD] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status/<search_id>')
def check_status(search_id):
    """Check search status and return results if available"""
    try:
        if search_id not in active_searches:
            return jsonify({
                'success': False,
                'error': 'Search ID not found'
            }), 404
        
        search_info = active_searches[search_id]
        
        # If completed, load CSV and return data
        if search_info['status'] == 'completed':
            csv_path = RESULTS_DIR / search_info['csv_filename']
            json_path = RESULTS_DIR / search_info['json_filename']
            
            if csv_path.exists():
                # Parse CSV and return data
                telegram_results = []
                online_results = []
                
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv_module.reader(f)
                    next(reader)  # Skip header
                    
                    for row in reader:
                        if row[0] == 'Telegram':
                            telegram_results.append(row[1:6])  # Link, Title, Views, Date, Duration
                        elif row[0] == 'Online Platform':
                            online_results.append(row[1:6])
                
                # Try to load statistics from JSON file
                statistics = {}
                if json_path.exists():
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                            statistics = json_data.get('statistics', {})
                            print(f"[API] Loaded statistics from JSON: {statistics}")
                    except Exception as e:
                        print(f"[API] Error loading JSON statistics: {str(e)}")
                
                # Parse statistics if available
                telegram_total_views = 0
                online_total_views = 0
                
                if statistics:
                    # Statistics are already extracted from the page
                    telegram_results_count = statistics.get('telegram_results', '0')
                    telegram_views_str = statistics.get('telegram_views', '0')
                    online_results_count = statistics.get('online_results', '0')
                    online_views_str = statistics.get('online_views', '0')
                    
                    print(f"[API] Raw statistics:")
                    print(f"  - Telegram Results: '{telegram_results_count}'")
                    print(f"  - Telegram Views: '{telegram_views_str}'")
                    print(f"  - Online Results: '{online_results_count}'")
                    print(f"  - Online Views: '{online_views_str}'")
                    
                    # Parse view counts (remove spaces and convert)
                    def parse_stat_number(num_str):
                        """Parse number from stat (e.g., '28 237' or '250K')"""
                        if not num_str:
                            return 0
                        try:
                            num_str = num_str.strip().replace(' ', '').replace(',', '').upper()
                            if 'K' in num_str:
                                return int(float(num_str.replace('K', '')) * 1000)
                            elif 'M' in num_str:
                                return int(float(num_str.replace('M', '')) * 1000000)
                            else:
                                return int(num_str)
                        except Exception as e:
                            print(f"[API] Error parsing '{num_str}': {str(e)}")
                            return 0
                    
                    telegram_total_views = parse_stat_number(telegram_views_str)
                    online_total_views = parse_stat_number(online_views_str)
                    
                    print(f"[API] Parsed view counts:")
                    print(f"  - Telegram Views: {telegram_total_views}")
                    print(f"  - Online Views: {online_total_views}")
                else:
                    print(f"[API] No statistics found, calculating from CSV...")
                    # Fallback: calculate from CSV if statistics not available
                    # Fallback: calculate from CSV if statistics not available
                    def parse_views(view_str):
                        """Parse view count string - handles '32K', '1.5M', '28 237', '1,234', etc."""
                        if not view_str or view_str == '-' or view_str == 'N/A':
                            return 0
                        
                        # Remove spaces and commas
                        view_str = view_str.strip().replace(' ', '').replace(',', '').upper()
                        
                        try:
                            if 'K' in view_str:
                                return float(view_str.replace('K', '')) * 1000
                            elif 'M' in view_str:
                                return float(view_str.replace('M', '')) * 1000000
                            elif 'B' in view_str:
                                return float(view_str.replace('B', '')) * 1000000000
                            else:
                                # Plain number (e.g., "28237" or "915")
                                return float(view_str)
                        except:
                            return 0
                    
                    # Calculate from CSV
                    telegram_total_views = sum(parse_views(row[2]) for row in telegram_results if len(row) > 2)
                    online_total_views = sum(parse_views(row[2]) for row in online_results if len(row) > 2)
                
                # Total views
                total_views = telegram_total_views + online_total_views
                
                return jsonify({
                    'success': True,
                    'status': 'completed',
                    'movie_name': search_info['movie_name'],
                    'csv_filename': search_info['csv_filename'],
                    'telegram_results': telegram_results,
                    'online_platform_results': online_results,
                    'total_telegram': len(telegram_results),
                    'total_online_platforms': len(online_results),
                    'telegram_total_views': int(telegram_total_views),
                    'online_total_views': int(online_total_views),
                    'total_views': int(total_views),
                    'statistics': statistics,  # Include raw statistics for reference
                    'completed_at': search_info.get('completed_at')
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'status': 'completed',
                    'error': 'CSV file not found'
                }), 500
        
        # If still running or failed
        return jsonify({
            'success': search_info['status'] != 'failed',
            'status': search_info['status'],
            'movie_name': search_info['movie_name'],
            'csv_filename': search_info['csv_filename'],
            'error': search_info.get('error'),
            'started_at': search_info.get('started_at')
        }), 200
        
    except Exception as e:
        print(f"[API] Status check error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



async def run_automation(movie_name: str, csv_filename: str, json_filename: str):
    """
    Run the Webkyte automation and return results
    
    Args:
        movie_name (str): Name of the movie to search
        csv_filename (str): Filename for CSV output
        json_filename (str): Filename for JSON output
        
    Returns:
        dict: Results including success status, data, and filenames
    """
    automation = None
    try:
        # Initialize automation
        automation = WebkyteMovieSearch(headless=True, timeout=30000)
        
        # Setup browser
        if not await automation.setup_browser():
            return {
                'success': False,
                'error': 'Failed to setup browser'
            }
        
        # Navigate to website
        if not await automation.navigate_to_site():
            await automation.cleanup()
            return {
                'success': False,
                'error': 'Failed to navigate to website'
            }
        
        # Search for movie
        if not await automation.search_movie(movie_name):
            await automation.cleanup()
            return {
                'success': False,
                'error': 'Failed to search for movie'
            }
        
        # Click DETECT COPIES button
        if not await automation.click_detect_copies():
            await automation.cleanup()
            return {
                'success': False,
                'error': 'Failed to click DETECT COPIES button'
            }
        
        # Collect links
        results = await automation.collect_links()
        
        if not results:
            await automation.cleanup()
            return {
                'success': False,
                'error': 'Failed to collect results'
            }
        
        # Save results to files in results directory
        json_filepath = RESULTS_DIR / json_filename
        
        # Get statistics from results if available
        statistics = results.get('statistics', {})
        
        output_data = {
            'movie_name': movie_name,
            'timestamp': datetime.now().isoformat(),
            'total_telegram_rows': len(results['telegram']),
            'total_online_platform_rows': len(results['online_platforms']),
            'telegram_data': results['telegram'],
            'online_platform_data': results['online_platforms'],
            'statistics': statistics  # Add extracted statistics
        }
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Save CSV
        csv_filepath = RESULTS_DIR / csv_filename
        
        print(f"[AUTOMATION] Saving CSV to: {csv_filepath.absolute()}")
        
        import csv
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers
            writer.writerow([
                'Platform', 'Link', 'Title', 'Views', 'Upload Date', 'Duration'
            ])
            
            # Write Telegram data
            for row in results['telegram']:
                telegram_row = ['Telegram'] + row
                while len(telegram_row) < 6:
                    telegram_row.append('')
                writer.writerow(telegram_row[:6])
            
            # Write Online Platform data
            for row in results['online_platforms']:
                online_row = ['Online Platform'] + row
                while len(online_row) < 6:
                    online_row.append('')
                writer.writerow(online_row[:6])
        
        print(f"[AUTOMATION] CSV saved successfully: {csv_filepath.absolute()}")
        print(f"[AUTOMATION] File exists: {csv_filepath.exists()}")
        print(f"[AUTOMATION] File size: {csv_filepath.stat().st_size if csv_filepath.exists() else 'N/A'} bytes")
        
        # Cleanup
        await automation.cleanup()
        
        return {
            'success': True,
            'movie_name': movie_name,
            'telegram_results': results['telegram'],
            'online_platform_results': results['online_platforms'],
            'total_telegram': len(results['telegram']),
            'total_online_platforms': len(results['online_platforms']),
            'csv_filename': csv_filename,
            'json_filename': json_filename,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        if automation:
            await automation.cleanup()
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    print("=" * 60)
    print("WEBKYTE MOVIE SEARCH - WEB SERVER")
    print("=" * 60)
    print("Starting Flask server...")
    print("Access the application at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
