# EVAL_REPORT v0.2.0-rag-eval
- Total: 70
- Valid: 25, Invalid: 25, Edge: 20
- Faithfulness avg: 0.94
- RAGAS target: >=0.8
- Confidence threshold: 0.75 -> ESCALATE if <0.75
- PII count: 0
- Flowlinx mentions: 0 (anonymized to VENUE_X)
- Sources: venue_x_stage1_spec_ANONYMIZED.md + venue_y_mifid2_ANONYMIZED.md
- Latency: <500ms retrieval (Vector+BM25+RRF)
