\# DEMO — 60 Sec Pocket Demo



Built for APIDays London — runs on laptop, no cloud needed.



\### Setup (first time)

```bash

git clone https://github.com/herestolu-rgb/fix-onboarding-mcp.git

cd fix-onboarding-mcp

pip install -r requirements.txt

ollama pull llama3.1:8b





Run Demo



```bash



\# Option 1: With sample log

python src/langgraph\_orchestrator.py --fix-log sample\_data/sample\_fix.log



\# Option 2: With your own log

python src/langgraph\_orchestrator.py --fix-log /path/to/your/fix.log



What You'll See



1. FIX log parsed + validated against onboarding rules
2. LLM summary (local Llama 3.1) — detects missing tags, sequence gaps
3. MCP tool calls logged
4. Final report: PASS/FAIL + remediation





Swap to Claude (prod)



```bash



export LLM\_PROVIDER=anthropic

export ANTHROPIC\_API\_KEY=sk-...

python src/langgraph\_orchestrator.py --fix-log sample.log

Pocket Demo Flow (for APIDays)



1. Open github.com/herestolu-rgb (pinned repo at top)
2. Open terminal, run command above
3. Show PASS/FAIL output in <10s



No API keys needed for local demo.

