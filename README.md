# Third Party Reports Downloader Bots
FastAPI service for bots that download transaction reports from NIBSS and INTERSWITCH report portals. The application is containerized with Docker for seamless deployment.
  
## Table of Contents
1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Local Development](#local-development)
4. [Docker Setup](#docker-setup)
5. [Configure Environment Variables](#configure-environment-variables)

## Features
__FastAPI Application:__ Enables bots to log in and download transaction reports from third-party platforms (Interswitch, NIBSS) using Waya Multilinks Technologies’ credentials.  

__Dockerized:__ Consistent, reproducible environments for local and production builds. 

## Project Structure
```bash
Transaction-Reports-Download-Bots/   
├── src/                      # Source code files 
│   ├── utils/                # Utility modules  
│   │   └── logger.py         # Logging utilities  
│   ├── enums.py              # Enum definitions  
│   ├── ISW_bot.py            # ISW bot main script  
│   └── NIP_bot.py            # NIP bot main script  
│  
├── .dockerignore             # Docker ignore file  
├── .env                      # Environment variables  
├── .gitignore                # Git ignore file  
├── Dockerfile                # Docker build instructions  
├── main.py                   # FastAPI entrypoint  
└── requirements.txt          # Python dependencies  
```

## Local Development
### 1. Clone the Repository:  
```bash
git clone https://github.com/Taiwo-Rachael/Transaction-Reports-Download-Bots.git
cd Transaction-Reports-Download-Bots
```
 
### 2. Create and Activate a Virtual Environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 4. Run Locally:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at http://127.0.0.1:8000.

## Docker Setup
### Build the Docker Image
```bash
docker build -t taiworachel/reports-downloader-bots .
```
### Run a Container
```bash
docker run --rm \
  -p 8000:8000 \
  --env-file .env \
  --env DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0.0 \
  -v ~/Downloads:/root/Downloads \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  taiworachel/reports-downloader-bots
```
The application is now available at http://localhost:8000

## Configure Environment Variables

In your project root, create a .env file and add the following variables:
```bash
NIP_USER
NIP_PW
NIP_PORTAL_URL
ISW_USER
ISW_PW
ISW_PORTAL_URL
```

