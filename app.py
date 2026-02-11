"""Flask API for Placement Profile Enricher."""
import os
import json
import tempfile
import shutil
from flask import Flask, request, send_file, jsonify, render_template
from werkzeug.utils import secure_filename
from zipfile import ZipFile
from config import Config
from utils.validators import allowed_file, validate_file_size, sanitize_url, validate_platform_url
from processor import ProfileEnricher
from scrapers import LeetCodeScraper, CodeforcesScraper, GitHubScraper

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE_BYTES

# Create necessary directories
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.PHOTOS_FOLDER, exist_ok=True)
os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)

# Global variable to store last processing summary
last_summary = None


@app.route('/', methods=['GET'])
def index():
    """Serve web interface."""
    return render_template('index.html')


@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint."""
    return jsonify({
        'name': 'Placement Profile Enricher API',
        'version': '1.0.0',
        'endpoints': {
            '/enrich': 'POST - Upload Excel file for enrichment',
            '/health': 'GET - Health check',
            '/api': 'GET - API information'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


@app.route('/enrich', methods=['POST'])
def enrich():
    """
    Enrich Excel file with profile data.
    
    Expects multipart/form-data with 'excel' file field.
    Returns ZIP file containing enriched.xlsx and summary.json
    """
    global last_summary
    
    # Validate file upload
    if 'excel' not in request.files:
        return jsonify({'error': 'No file provided. Use field name "excel"'}), 400
    
    file = request.files['excel']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(Config.ALLOWED_EXTENSIONS)}'}), 400
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(temp_dir, filename)
        file.save(input_path)
        
        # Validate file size
        file_size = os.path.getsize(input_path)
        valid, error = validate_file_size(file_size)
        if not valid:
            return jsonify({'error': error}), 400
        
        # Process file
        enricher = ProfileEnricher()
        output_path = os.path.join(temp_dir, 'enriched.xlsx')
        
        success, error = enricher.process_file(input_path, output_path)
        
        if not success:
            return jsonify({'error': error}), 500
        
        # Get summary and store it globally
        summary = enricher.get_summary()
        last_summary = summary
        
        summary_path = os.path.join(temp_dir, 'summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Create ZIP file
        zip_path = os.path.join(temp_dir, 'result.zip')
        with ZipFile(zip_path, 'w') as zipf:
            zipf.write(output_path, 'enriched.xlsx')
            zipf.write(summary_path, 'summary.json')
        
        # Send ZIP file
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name='enriched_profiles.zip'
        )
    
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    
    finally:
        # Cleanup temporary directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


@app.route('/analyze_urls', methods=['POST'])
def analyze_urls():
    """
    Analyze individual profile URLs.
    
    Expects JSON with optional fields: leetcode, codeforces, github
    Returns JSON with analysis results for each platform
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        results = {}
        
        # Initialize scrapers
        leetcode_scraper = LeetCodeScraper()
        codeforces_scraper = CodeforcesScraper()
        github_scraper = GitHubScraper()
        
        # Process LeetCode URL
        if data.get('leetcode'):
            url = sanitize_url(data['leetcode'])
            if url and validate_platform_url(url, 'leetcode'):
                success, result = leetcode_scraper.scrape(url)
                results['leetcode'] = {
                    'success': success,
                    'data': result if success else None,
                    'error': result if not success else None
                }
            else:
                results['leetcode'] = {
                    'success': False,
                    'data': None,
                    'error': 'Invalid LeetCode URL'
                }
        
        # Process Codeforces URL
        if data.get('codeforces'):
            url = sanitize_url(data['codeforces'])
            if url and validate_platform_url(url, 'codeforces'):
                success, result = codeforces_scraper.scrape(url)
                results['codeforces'] = {
                    'success': success,
                    'data': result if success else None,
                    'error': result if not success else None
                }
            else:
                results['codeforces'] = {
                    'success': False,
                    'data': None,
                    'error': 'Invalid Codeforces URL'
                }
        
        # Process GitHub URL
        if data.get('github'):
            url = sanitize_url(data['github'])
            if url and validate_platform_url(url, 'github'):
                success, result = github_scraper.scrape(url)
                results['github'] = {
                    'success': success,
                    'data': result if success else None,
                    'error': result if not success else None
                }
            else:
                results['github'] = {
                    'success': False,
                    'data': None,
                    'error': 'Invalid GitHub URL'
                }
        
        if not results:
            return jsonify({'error': 'No valid URLs provided'}), 400
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/last_summary', methods=['GET'])
def get_last_summary():
    """
    Get the last processing summary.
    
    Returns the summary from the last Excel file processing
    """
    global last_summary
    
    if last_summary is None:
        return jsonify({
            'total_rows': 0,
            'total_duration_ms': 0,
            'platforms': {}
        })
    
    return jsonify(last_summary)


if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.FLASK_DEBUG
    )

