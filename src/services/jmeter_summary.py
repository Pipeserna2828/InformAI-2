import csv, io, time
from typing import Dict, Any, List, Tuple
from src.domain.summary_contract import Summary, OverallMetrics, MethodMetrics, Latency
from src.core.percentiles import percentile
from src.core.time_utils import duration_ms_from_timestamps

def _to_bool(v: str) -> bool:
    s = str(v).strip().lower()
    return s in ("true", "1", "y", "yes", "t")

def build_summary_from_jmeter(csv_bytes: bytes) -> Tuple[Summary, Dict[str, bool]]:
    s = io.StringIO(csv_bytes.decode("utf-8", errors="replace"))
    reader = csv.DictReader(s)
    headers = reader.fieldnames or []
    required = {"timeStamp", "label", "elapsed", "success"}
    missing = [h for h in required if h not in headers]
    if missing:
        raise KeyError(f"Archivo JMeter incompleto. Faltan columnas: {missing}")

    rows: List[Dict[str, Any]] = []
    for row in reader:
        try:
            rows.append({
                "ts": int(row["timeStamp"]),
                "label": str(row["label"]),
                "elapsed": float(row["elapsed"]),
                "ok": _to_bool(row["success"])
            })
        except Exception:
            continue

    requests = len(rows)
    failures = sum(1 for r in rows if not r["ok"])
    error_rate = round(failures / max(requests, 1), 4)

    timestamps = [r["ts"] for r in rows]
    duration_ms = duration_ms_from_timestamps(timestamps)
    throughput = (requests / (duration_ms/1000.0)) if duration_ms else 0.0

    latencies = [r["elapsed"] for r in rows]
    lat = Latency(
        p50=percentile(latencies, 0.50),
        p90=percentile(latencies, 0.90),
        p95=percentile(latencies, 0.95),
        p99=percentile(latencies, 0.99),
    )

    overall = OverallMetrics(
        name="(overall)",
        requests=requests,
        failures=failures,
        error_rate=error_rate,
        duration_ms=duration_ms,
        throughput_rps=throughput,
        latency_ms=lat,
    )

    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        buckets.setdefault(r["label"], []).append(r)

    by_method: List[MethodMetrics] = []
    for name, recs in sorted(buckets.items()):
        req = len(recs)
        fai = sum(1 for x in recs if not x["ok"])
        er = round(fai / max(req, 1), 4)
        ts = [x["ts"] for x in recs]
        dur = duration_ms_from_timestamps(ts)
        thr = (req / (dur/1000.0)) if dur else 0.0
        latv = [x["elapsed"] for x in recs]
        by_method.append(MethodMetrics(
            name=name,
            requests=req,
            failures=fai,
            error_rate=er,
            duration_ms=dur,
            throughput_rps=thr,
            latency_ms=Latency(
                p50=percentile(latv, 0.50),
                p90=percentile(latv, 0.90),
                p95=percentile(latv, 0.95),
                p99=percentile(latv, 0.99),
            ),
        ))

    flags = {"approximated_percentiles": False, "approximated_duration": False, "approximated_failures": False}
    run_id = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return Summary(tool="jmeter", run_id=run_id, overall=overall, by_method=by_method), flags
