"""
Author: Shawny

Export webpage content to PDF format
"""
import re
import yaml
from pathlib import Path
import threading
import time
import sys

from ms_test_stats.scanner import collect_sources
from ms_test_stats.parser import extract_testcases_from_file
from ms_test_stats.stats import build_dataframes
from ms_test_stats.excel import write_excel
from ms_test_stats.webapp import create_app


def export_webpage_to_pdf(url: str, output_path: str, wait_time: int = 3000) -> None:
    """
    Export webpage content from the specified URL to a PDF file
    
    Args:
        url: The webpage URL to export
        output_path: Path for the output PDF file
        wait_time: Time to wait for page rendering (milliseconds), default 3000ms
    """
    # Check if Playwright is installed
    try:
        from playwright.sync_api import sync_playwright, Error as PlaywrightError
    except ImportError:
        print("\n" + "="*70)
        print("ERROR: Playwright is not installed")
        print("="*70)
        print("Please run the following commands to install:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print("="*70 + "\n")
        sys.exit(1)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Accessing webpage: {url}")
    print(f"[INFO] Output file: {output_file}")
    
    try:
        with sync_playwright() as p:
            # Launch browser
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                error_msg = str(e)
                if "Executable doesn't exist" in error_msg or "chrome-headless-shell" in error_msg:
                    print("\n" + "="*70)
                    print("ERROR: Playwright browser is not installed")
                    print("="*70)
                    print("Browser executable not found. Please run the following command to install:")
                    print("  playwright install chromium")
                    print("\nOr install all browsers:")
                    print("  playwright install")
                    print("="*70 + "\n")
                    sys.exit(1)
                else:
                    print(f"\n[ERROR] Failed to launch browser: {e}")
                    print("Please try running: playwright install chromium\n")
                    sys.exit(1)
            
            try:
                # Create new page
                page = browser.new_page(viewport={"width": 1400, "height": 900})
                
                # Navigate to webpage with retry mechanism
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        print(f"[INFO] Loading webpage... (attempt {attempt + 1}/{max_retries})")
                        page.goto(url, wait_until="networkidle", timeout=15000)
                        break
                    except PlaywrightError as e:
                        if attempt < max_retries - 1:
                            print(f"[WARN] Load failed, retrying in 2 seconds...")
                            time.sleep(2)
                        else:
                            raise RuntimeError(f"Failed to load webpage after {max_retries} attempts: {e}") from e
                
                # Wait for page to fully render (especially for dynamic content like charts)
                print(f"[INFO] Waiting for page rendering to complete... ({wait_time}ms)")
                page.wait_for_timeout(wait_time)
                
                # Generate PDF
                print("[INFO] Generating PDF...")
                page.pdf(
                    path=str(output_file),
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "1cm",
                        "right": "1cm",
                        "bottom": "1cm",
                        "left": "1cm"
                    }
                )
                
                print(f"[OK] PDF successfully saved to: {output_file}")
                
            finally:
                browser.close()
                
    except Exception as e:
        print(f"\n[ERROR] Failed to export PDF: {e}")
        print(f"Error type: {type(e).__name__}")
        raise


def wait_for_server(url: str, max_wait: int = 30, check_interval: int = 1) -> bool:
    """
    Wait for server to start and become available
    
    Args:
        url: Server URL
        max_wait: Maximum wait time in seconds
        check_interval: Check interval in seconds
    
    Returns:
        True if server is available, False otherwise
    """
    import requests
    
    print(f"[INFO] Waiting for server to start: {url}")
    
    for i in range(max_wait):
        try:
            response = requests.get(url, timeout=check_interval)
            if response.status_code == 200:
                print(f"[OK] Server is ready")
                return True
        except Exception:
            if i < max_wait - 1:
                time.sleep(check_interval)
                if (i + 1) % 5 == 0:
                    print(f"[INFO] Waiting... ({i + 1}/{max_wait} seconds)")
            else:
                print(f"[ERROR] Server failed to start within {max_wait} seconds")
                return False
    
    return False


def main():
    """Main function: Generate statistics and export to PDF"""
    # Read configuration
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    
    repo_root = Path(cfg["repo_root"]).resolve()
    tests_root = repo_root / cfg.get("tests_dir", "tests")
    out_excel = cfg.get("output_excel", "output/stats.xlsx")
    out_pdf = cfg.get("output_pdf", "output/dashboard.pdf")
    
    print("="*70)
    print("MindSpore Test Statistics - PDF Export Tool")
    print("="*70)
    
    # Collect test cases
    print("\n[Step 1/4] Scanning test files...")
    level_re = re.compile(cfg.get("level_regex", r"^level\d+$"))
    sources = collect_sources(tests_root)
    
    print(f"[Step 2/4] Parsing test cases...")
    cases = []
    for py_path, src in sources:
        try:
            cases.extend(extract_testcases_from_file(py_path, src, level_re))
        except SyntaxError:
            continue
    
    print(f"[Step 3/4] Generating statistics...")
    dfs = build_dataframes(cases, cfg["device_keywords"], str(tests_root))
    write_excel(out_excel, **dfs)
    print(f"[OK] Excel file generated: {out_excel}")
    
    # Start web server
    print(f"\n[Step 4/4] Starting web server and exporting PDF...")
    app = create_app(out_excel)
    
    def run_server():
        """Run Flask server in background thread"""
        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    server_url = "http://127.0.0.1:5000/"
    if not wait_for_server(server_url, max_wait=30):
        print("[ERROR] Failed to start server, exiting")
        sys.exit(1)
    
    # Export PDF
    try:
        export_webpage_to_pdf(server_url, out_pdf, wait_time=3000)
    finally:
        # Try to shutdown server
        try:
            import requests
            requests.get("http://127.0.0.1:5000/shutdown", timeout=2)
        except Exception:
            pass
    
    print("\n" + "="*70)
    print("PDF export completed!")
    print("="*70)


if __name__ == "__main__":
    main()
