DEMO — 60 Sec Pocket Demo
Built for APIDays London — runs on laptop, no cloud needed.
Setup (first time)
```bash
git clone https://github.com/herestolu-rgb/fix-onboarding-mcp.git
cd fix-onboarding-mcp
pip install -r requirements.txt
ollama pull llama3.1:8b
```
Run Demo
```bash
python langgraph_agent_with_llm.py --fix-log /path/to/your/fix.log
```
> Note: a bundled sample FIX log isn't in the repo yet. For now, point `--fix-log` at
> a FIX log of your own. (TODO before APIDays: add `sample_data/sample_fix.log` so
> this becomes a true zero-setup one-liner.)
What You'll See
FIX log parsed and validated against onboarding rules
LLM summary (local Llama 3.1) — detects missing tags, sequence gaps
MCP tool calls logged
Final report: PASS/FAIL + remediation
Swap to Claude (planned, not yet live)
The agent's LLM backend is pluggable via `LLM_PROVIDER`. An Anthropic/Claude
backend is planned but not yet tested end-to-end — it requires billing setup
that hasn't been done yet. Once verified, the swap will look like:
```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-...
python langgraph_agent_with_llm.py --fix-log /path/to/your/fix.log
```
Until that's confirmed working, treat this as a preview of the design, not a
step to run.
Pocket Demo Flow (for APIDays)
Open github.com/herestolu-rgb (pinned repo at top)
Open terminal, run the setup + run commands above (with your own FIX log)
Show PASS/FAIL output
No API keys needed for the local demo.
