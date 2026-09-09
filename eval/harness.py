import json
from rag.fix_spec_rag import FIXSpecRAG

rag = FIXSpecRAG()

def evaluate():
    scores = {"clean": [], "medium": [], "messy": []}
    with open("eval/golden.jsonl") as f:
        for line in f:
            case = json.loads(line)
            ctx = rag.retrieve(case["input"])
            result = rag.validate_with_context(case["input"], ctx)
            # Metrics Ethos scores: faithfulness, context precision, tool accuracy
            acc = result["context_precision"]
            scores[case["complexity"]].append(acc)
            print(f"{case['case_id']} {case['complexity']} prec={acc} conf={case['parse_confidence']}")
    print("Summary:", {k: sum(v)/len(v) for k,v in scores.items() if v})

if __name__ == "__main__":
    evaluate()