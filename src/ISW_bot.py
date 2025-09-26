from playwright.async_api import async_playwright
from datetime import datetime, date
from dotenv import load_dotenv
from src.utils.logger import log_and_store
from typing import Optional
from pathlib import Path
import traceback
import logging
import os

# Detect system default Downloads folder or use env override
DOWNLOAD_DIR = Path.home() / "Downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = Path(__file__).resolve().parent / "log_file.logs"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)  # ensure the directory exists

# logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# configure evironment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

USERNAME = os.getenv("ISW_USER")     
PASSWORD = os.getenv("ISW_PW")
PORTAL_URL = os.getenv("ISW_PORTAL_URL", "").strip().strip('"').strip("'")

# credentials validation
if not USERNAME or not PASSWORD:
    raise ValueError("Missing ISW_USER or ISW_PW. Check your .env file.")

if not PORTAL_URL:
    raise ValueError("Missing PORTAL_URL. Check your .env file.")

# Main automation
async def isw_run(
        start_date: date,
        end_date  : date,
        headless: bool = False,
        report_code: Optional[str] = None
) -> None:

    messages = []
    total_saved = 0
    max_attempts = 5
    attempts = 0

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Login 
            log_and_store("Navigating to login …", messages, level="info")
            await page.goto(f"{PORTAL_URL}", timeout=90000)  # Ensure correct login page
            await page.wait_for_load_state("domcontentloaded", timeout=90000)
            await page.wait_for_selector("a.passport-button", timeout=90000)
            await page.click("a.passport-button", timeout=90000) # Click the login button
            
            # Wait until the username and password inputs are visible
            await page.wait_for_selector("#username", timeout=90000)
            await page.wait_for_selector("#password", timeout=90000)
            await page.fill("#username", USERNAME)
            await page.fill("#password", PASSWORD)
            await page.click("button.btn-dark-blue:has-text('Sign in')") #< Login
            await page.wait_for_timeout(3000)  # Wait 3 seconds for frameset to load

            # Frames
            header_frame = page.frame(name="header")
            menu_frame = page.frame(name="menu")
            body_frame = page.frame(name="body")

            await page.wait_for_timeout(3000)  # wait for the page to load

            # Navigate to Transaction Report 
            menu_frame = menu_frame
            if not menu_frame:
                log_and_store("Could not find a frame containing the Reports menu!", messages, level="error")
                return
            
            await menu_frame.wait_for_selector("td.menuLink:has-text('Reports')", timeout=10000)
            await menu_frame.click("td.menuLink:has-text('Reports')")

            # Wait for and click Reports Root link
            await menu_frame.wait_for_selector("a.innerLink:has-text('Reports Root')", timeout=10000)
            await menu_frame.click("a.innerLink:has-text('Reports Root')")
            
            # Set date range
            while True:
                today = datetime.today().date()
                if (today - start_date).days > 90:
                    log_and_store("You cannot download reports older than 90 days. Enter a date range within the last 90 days.", messages, level="error")
                    continue
                break  # valid dates, exit loop

            # Wait for input fields to be available
            await body_frame.wait_for_selector("input[name='dateStart']", timeout=10000)
            await body_frame.wait_for_selector("input[name='dateEnd']", timeout=10000)
            
            # Fill start and end dates  
            await body_frame.evaluate(
                """(date) => {
                    const el = document.querySelector("input[name='dateStart']");
                    el.value = date;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }""",
                start_date.strftime("%d/%m/%Y")
            )
            await body_frame.evaluate(
                """(date) => {
                    const el = document.querySelector("input[name='dateEnd']");
                    el.value = date;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }""",
                end_date.strftime("%d/%m/%Y")
            )
            log_and_store(f"Calendar dates filled and applied", messages, level="info")  # append to logs and messages

            # Wait for the select to be available
            await body_frame.wait_for_selector("select#reportTypeId", timeout=10000)
            await body_frame.select_option("select#reportTypeId", value=report_code)
            await page.wait_for_timeout(500)  # short wait to ensure dropdown change is registered
            log_and_store(f"Report type set to: {report_code}", messages, level="info")

            # Trigger the search
            await body_frame.click("input#search")
            await body_frame.wait_for_timeout(2000)  # Wait for the table to reload
            log_and_store("Search triggered by button click", messages, level="info") 
              
            # Check if any download button is present
            await body_frame.wait_for_timeout(2000)
            download_btn = body_frame.locator("a[href*='reportDownload.do']")
            if await download_btn.count() == 0:
                attempts += 1
                log_and_store("No reports found for this type and date range.", messages, level="error")

                if attempts >= max_attempts:
                    log_and_store("Maximum number of attempts exceeded.", messages, level="error")
                    await browser.close()
                    return {
                        "status": "no report available",
                        "total_saved": total_saved,
                        "messages": messages,
                    }
                
                await browser.close()
                return {
                    "status": "no report available",
                    "total_saved": 0,
                    "messages": messages,
                    "prompt": "No reports found. Please choose to either try another report type or a different date range."
                }
             
            else:
                log_and_store("Table reloaded – starting downloads", messages, level="info")
                  #break  # Exit loop and continue with downloads
                
            # Download reports 
            page_num = 1
            while True:
                # Collect all download buttons currently visible in this page of the table
                await body_frame.locator("a[href*='reportDownload.do']").first.wait_for(state="visible", timeout=60_000)   
                links   = await body_frame.locator("a[href*='reportDownload.do']").all()
                count   = len(links)
                if count == 0:
                    print("⚠️  no download buttons found on this page")
                    break
                
                log_and_store(f"Page {page_num} – {count} download links found", messages, level="info")  # append to logs and messages
                for i, link in enumerate(links):
                    try:
                        await page.wait_for_timeout(2_000)  # give button time to activate
                        async with page.expect_download(timeout=120_000) as dl_info:
                            await link.click(force=True)
                            
                        dl = await dl_info.value
                        MAX_PATH = 259
            
                        # max_filename_len = MAX_PATH - len(str(DOWNLOAD_DIR)) - 1  # -1 for the separator
                        filename = dl.suggested_filename
                        name, ext = os.path.splitext(filename)
                        # Check if the filename exceeds the maximum windows path length of 260
                        if len(str(DOWNLOAD_DIR / filename)) > MAX_PATH:
                            # if it exceeds, select from the 25th character to the end (i.e, ecxlude the 1st 24 characters)
                            filename = name[24:] + ext
                            # filename = name[:max_filename_len] + ext
                    
                        save_path = DOWNLOAD_DIR / filename
                        # save_path = DOWNLOAD_DIR / dl.suggested_filename
                        await dl.save_as(save_path)
                        total_saved += 1
                        log_and_store(f"⬇️  {total_saved:>3} saved {save_path.name}", messages, level="info")  # append to logs and messages
                        await page.wait_for_timeout(1000)  # short delay between downloads
                    except Exception as e:
                        log_and_store(f" ⚠️ Download failed for link {i + 1} — {e}", messages, level="warning") # append to logs and messages

                # next page?
                next_btn = body_frame.locator("a:has-text('Next')")
                if await next_btn.count() == 0:
                    break
                page_num += 1
                print(f"➡️  Page {page_num}")
                await next_btn.first.click()
                await page.wait_for_timeout(500)
                await body_frame.locator("tbody tr").first.wait_for(state="visible", timeout=10_000)

            log_and_store(f"Finished – {total_saved} files downloaded.", messages, level="info")  # append to logs and messages
            await context.close()
            await browser.close()
            return {
                "status": "success" if total_saved > 0 else "warning",
                "start_date": start_date,
                "end_date": end_date,
                "files_downloaded": total_saved,
                "messages": messages,
                "download_directory": str(DOWNLOAD_DIR) 
            }

    except Exception as e:
        tb = traceback.format_exc()
        log_and_store(f"Error during download: {e}\n{tb}", messages, level="error")
        return {"messages": messages, "total_saved": total_saved}

