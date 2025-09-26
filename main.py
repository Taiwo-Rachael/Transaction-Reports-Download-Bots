from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Query, HTTPException
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.NIP_bot import nip_run
from src.ISW_bot import isw_run
from src.enums import ReportType
from src.ISW_bot import DOWNLOAD_DIR as isw_download_dir
from src.NIP_bot import DOWNLOAD_DIR as nip_download_dir
import traceback
import os

print(f"USER: {os.getenv('NIP_USER')},PASSWORD: {os.getenv('NIP_PW')}")
print(f"ISW_USER:{os.getenv('ISW_USER')}, ISW_PW: {os.getenv('ISW_PW')}")

app = FastAPI(
    title="Transaction Reports Downloader API",
    version="1.0.0",
    description="Bots for Downloading Reports",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint to download NIP reports
@app.post("/download-nip-report")
async def download_nip_report(
    start_date: str = Query(..., description="Format: YYYY-MM-DD"),
    end_date: str = Query(..., description="Format: YYYY-MM-DD"),
    headless: bool = False
):
    try:
        # Convert string to date object
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt   = datetime.strptime(end_date, "%Y-%m-%d").date()

        result = await nip_run(start_date=start_dt, end_date=end_dt, headless=headless)

        status_code = 200
        status_text = "success" if status_code == 200 else "failed"

        return JSONResponse(
            status_code=status_code,
            content={
                "status": status_text,
                "start_date": str(start_dt),
                "end_date": str(end_dt),
                "files_downloaded": result.get("total_saved", 0),
                "download_directory": str(nip_download_dir),
                "messages": result.get("messages", [])
            }
        )

    except Exception as e:
        tb = traceback.format_exc()
        error_message = f"Error during download: {e}\n{tb}"
        print(error_message)  # log to console
        raise HTTPException(status_code=500, detail=error_message)

# Endpoint to download ISW reports
@app.post("/download-isw-reports")
async def download_isw_reports(
    start_date: str = Query(..., description="Format: YYYY-MM-DD"),
    end_date: str = Query(..., description="Format: YYYY-MM-DD"),
    report_type: ReportType = Query(..., description="Select report type"),
    headless: bool = False,
):
    try:
        report_code = report_type.name.lstrip("_")
        start_dte = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dte   = datetime.strptime(end_date, "%Y-%m-%d").date()
        result = await isw_run(start_date=start_dte, end_date=end_dte, report_code=report_code, headless=headless)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "start_date": str(start_dte),
                "end_date": str(end_dte),
                "report_type": report_type.value,
                "files_downloaded": result.get("total_saved", 0),
                "download_directory": str(isw_download_dir),
                "messages": result.get("messages", [])
            }
        )

    except Exception as e:
        tb = traceback.format_exc()
        error_message = f"Error during download: {e}\n{tb}"
        print(error_message)

