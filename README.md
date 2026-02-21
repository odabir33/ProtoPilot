# ProtoPilot
Turning Product Vision into Working Prototypes

## Agents Set Up
```python

#Docs Link
https://google.github.io/adk-docs/get-started/quickstart/

# create virtual environment inside /backed/agents
python -m venv .venv 

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
```