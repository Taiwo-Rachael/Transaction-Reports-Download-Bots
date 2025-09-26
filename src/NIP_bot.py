from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from src.utils.logger import log_and_store
import traceback
import logging
import os

# Detect system default Downloads folder or use env override
DOWNLOAD_DIR = Path.home() / "Downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = Path(__file__).resolve().parent / "log_file.logs"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)  # ensure the directory exists

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# configuring environment variables
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

USERNAME   = os.getenv("NIP_USER")
PASSWORD   = os.getenv("NIP_PW")
NIP_PORTAL_URL = os.getenv("NIP_PORTAL_URL", "").strip().strip('"').strip("'")

# credentials validation
if not USERNAME or not PASSWORD:
    raise ValueError("Missing NIP_USER or NIP_PW in environment")
if not NIP_PORTAL_URL:
    raise ValueError("Missing NIP_PORTAL_URL in environment")

# Main automation
async def nip_run(start_date: date,
                  end_date  : date,
                  headless: bool = False
) -> None:
    
    messages = []
    total_saved = 0
    try:

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            # Login
            log_and_store("Navigating to login …", messages, level="info") #append to logs and messages

            await page.goto(f"{NIP_PORTAL_URL}/main.jspx", timeout=900000)
            await page.wait_for_selector("#email",timeout=900000)
            await page.fill("#email", USERNAME,timeout=900000)
            await page.fill("#password", PASSWORD, timeout=90000)
            await page.click("button:has-text('Login')", timeout=90000)

            # Report menu
            await page.click("text=Report")
            await page.click("text=Transaction Report")
            await page.wait_for_selector("text=Transaction Report :: List")

            # Date range
            log_and_store(f"📅  From: {start_date:%d/%m/%Y}", messages,level="info") #append to logs and messages
            log_and_store(f"📅  To:   {end_date:%d/%m/%Y}", messages,level="info")

            await page.click("#settlementDateFilter")
            await page.click("#settlementDateFilter")
            await page.fill("input[name='daterangepicker_start']",
                    start_date.strftime("%d/%m/%Y"), force=True)
            await page.fill("input[name='daterangepicker_end']",
                    end_date.strftime("%d/%m/%Y"),   force=True)
            await page.wait_for_timeout(3_000)
            await page.click("button:has-text('Apply')")
            await page.wait_for_timeout(3_000) #< wait for the page to update

            # Trigger table reload
            await page.evaluate("window.transactionReportTable.reload()") #< this is the JS function that reloads the table
            await page.wait_for_timeout(3_000) #< wait for the table to reload
            log_and_store("Reload triggered", messages,level="info") #append to logs and messages

            # Download loop
            download_btn = page.locator("a:has(i.fa-download), button:has(i.fa-download)")
            await download_btn.first.wait_for(state="visible", timeout=15_000)
            log_and_store("Table ready – starting downloads", messages,level="info") #append to logs and messages

            total_saved = 0
            page_num    = 1

            while True:
                await page.wait_for_timeout(2000)  # give time for table to settle
                await page.locator("tbody tr").first.wait_for(state="visible", timeout=10_000)
            
                # Collect all download buttons currently visible in this page of the table
                links   = page.locator("a:has(i.fa-download), button:has(i.fa-download)")
                count   = await links.count()
                log_and_store(f"Found {count} download buttons on page {page_num}", messages, level="info")  # append to logs and messages

                if count == 0:
                    log_and_store("⚠️  no download buttons found on this page", messages, level="warning")  # append to logs and messages
                    break

                for i in range(count):
                    link = links.nth(i)
                    try:
                        await link.wait_for(state="visible", timeout=5000)  # give button time to activate
                        await link.scroll_into_view_if_needed() 
                        async with page.expect_download(timeout=60_000) as dl_info:
                            await link.click(force=True,timeout=60_000)

                        dl = await dl_info.value
                        filename = dl.suggested_filename #extract file name
                        save_path = DOWNLOAD_DIR / filename 

                        await dl.save_as(save_path) # save file
                        total_saved += 1
                        log_and_store(f"⬇️  {total_saved:>3} saved {save_path.name}", messages, level="info") # append to logs and messages
                        
                        await page.wait_for_timeout(1000)  # short delay between downloads
                   
                    except Exception as e:
                        log_and_store(f"⚠️  Download failed for link {i + 1} — {e}", messages, level="warning") # append to logs and messages
                        continue

                # next page?
                next_btn = page.locator("li.paginate_button:has-text('Next'):not(.disabled) a")
                if await next_btn.count() == 0:
                    break
                page_num += 1
                log_and_store(f"➡️  Page {page_num}", messages, level="info") # append to logs and messages

                await next_btn.first.click() #click the next button (the first one)
                await page.wait_for_timeout(1_000) # give one second for page to settle
                await page.evaluate("window.scrollTo(0, 0)")  #force scroll to top ###
                await page.locator("tbody tr").first.wait_for(state="visible", timeout=5_000)

            log_and_store(f"Finished – {total_saved} files downloaded.", messages, level="info") # append to logs and messages
            await browser.close()
            return {
                "status": "success" if total_saved > 0 else "warning",
                "start_date": start_date,
                "end_date": end_date,
                "files_downloaded": total_saved,
                "messages": messages
            }

    except Exception as e:
        tb = traceback.format_exc()
        log_and_store(f"Error during download: {e}\n{tb}", messages, level="error")
        return {"messages": messages, "total_saved": total_saved}