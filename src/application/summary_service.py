import json
from src.services.k6_summary import build_summary_from_k6
from src.services.jmeter_summary import build_summary_from_jmeter
from src.domain.summary_contract import Summary

def detect_and_build_summary(file_bytes: bytes, filename: str, content_type: str) -> tuple[Summary, dict]:
    # JSON → K6
    if content_type == "application/json" or filename.lower().endswith(".json"):
        try:
            json.loads(file_bytes.decode("utf-8", errors="strict"))
        except Exception:
            raise ValueError("JSON ilegible o corrupto.")
        return build_summary_from_k6(file_bytes)

    # CSV → JMeter
    return build_summary_from_jmeter(file_bytes)