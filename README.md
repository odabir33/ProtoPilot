# ProtoPilot
Turning Product Vision into Working Prototypes

## Agents Set Up
```python

#Docs Link
https://google.github.io/adk-docs/get-started/quickstart/



# create virtual environment inside /backed/agents
python -m venv .venv 

# activate virtual environment

source .venv/bin/activate # MacOS or Linux

.venv\Scripts\activate.bat # Windows



# install deps
pip install -r requirements.txt

# set your Groq API Key inside .env file inside each agent folder
GROQ_API_KEY='your_api_key_here'

# run agents with Google ADK UI for testing
adk web

# expose agents via API
adk api_server

```