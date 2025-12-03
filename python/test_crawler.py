import asyncio
import os
import sys
from crawl4ai import AsyncWebCrawler, BrowserConfig

# Force verbose logging for playwright
os.environ["DEBUG"] = "pw:api"

async def test():
    print("Starting crawler test...", flush=True)
    
    try:
        print("Configuring BrowserConfig...", flush=True)
        browser_config = BrowserConfig(
            headless=True,
            verbose=True,
            browser_type="chromium",
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu",
            ]
        )
        
        print("Creating AsyncWebCrawler...", flush=True)
        crawler = AsyncWebCrawler(config=browser_config)
        
        print("Entering context (launching browser)...", flush=True)
        # Set a timeout to detect hangs
        try:
            async with asyncio.timeout(30):
                await crawler.__aenter__()
            print("Context entered successfully!", flush=True)
            
            print("Exiting context...", flush=True)
            await crawler.__aexit__(None, None, None)
            print("Test PASSED", flush=True)
            
        except TimeoutError:
            print("TIMEOUT: Browser launch took longer than 30 seconds", flush=True)
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test())
