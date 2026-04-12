# ProtoPilot
Turning Product Vision into Working Prototypes

## Agents Set Up
```python

#Docs Link
https://google.github.io/adk-docs/get-started/quickstart/

# create virtual environment inside /backed/agents
python3 -m venv .venv 

# activate virtual environment
# MacOS or Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate.bat 

# install deps
pip install -r requirements.txt

# set env variables inside .env file inside /agents
# refer .example.env file for reference

# run agents with Google ADK UI for testing (inside /agents folder)
adk web

# expose agents via API (inside /agents folder)
adk api_server

# Start FastAPI dev server
fastapi dev api/server.py
```

## Backend Run


# go to backend folder
cd backend

# create virtual environment
# MacOS or Linux
python3 -m venv .venv

# Windows
python -m venv .venv

# activate virtual environment
# MacOS or Linux
source .venv/bin/activate

# Windows
. .\.venv\Scripts\Activate.ps1

# Windows CMD 
.venv\Scripts\activate.bat

# install backend deps
pip install -r requirements.txt

# run backend server
uvicorn api.server:app --reload --port 8000

# health check
# open in browser:
http://127.0.0.1:8000/health

## Frontend Run

# open a new terminal and go to frontend folder
cd frontend

# install frontend deps
npm install

# run frontend
npm start

# open in browser:
http://localhost:4200

## Available Models For Our Team
```
gemini-2.0-flash-001-litellm-usc1
gemini-2.0-flash-001-litellm-usw1
gemini-2.0-flash-lite-001-litellm-usc1
gemini-2.0-flash-lite-001-litellm-usw1
gemini-2.5-flash-litellm-usc1
gemini-2.5-flash-litellm-usw1
gemini-2.5-flash-lite-litellm-usc1
gemini-2.5-flash-lite-litellm-usw1
gemini-2.5-pro-litellm-usc1
gemini-2.5-pro-litellm-usw1
claude-sonnet-4@20250514-litellm-use5
claude-sonnet-4-6-litellm-use5
imagen-3.0-generate-002-litellm-usc1
text-embedding-005-litellm-usc1
text-embedding-005-litellm-usw1
llama-4-maverick-17b-128e-instruct-maas-litellm-use5
```
