import json, time
from typing import Any, Dict, List, Tuple
from src.domain.summary_contract import Summary, OverallMetrics, MethodMetrics, Latency

def _safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)

def _latency_from_metric_dict(m: Dict[str, Any]) -> Latency:
    p50 = _safe_float(m.get("med", m.get("p(50)", 0.0)))
    p90 = _safe_float(m.get("p(90)", 0.0))
    p95 = _safe_float(m.get("p(95)", 0.0))
    p99 = _safe_float(m.get("p(99)", 0.0))
    return Latency(p50=p50, p90=p90, p95=p95, p99=p99)

def _method_metric_key(method_name: str) -> str:
    return "Metodo_" + method_name.replace(".", "_").replace("/", "_") + "_duration"

def _extract_counts(data: Dict[str, Any]):
    metrics = data.get("metrics", {})
    per_method = {}
    total_req = 0
    total_fail = 0
    rg_checks = data.get("root_group", {}).get("checks", {})
    if rg_checks:
        for check_name, payload in rg_checks.items():
            method_name = check_name.replace(" OK", "")
            passes = int(payload.get("passes", 0))
            fails = int(payload.get("fails", 0))
            per_method[method_name] = {"requests": passes + fails, "failures": fails}
            total_req += passes + fails
            total_fail += fails
    else:
        if "checks" in metrics:
            total_req = int(metrics["checks"].get("passes", 0)) + int(metrics["checks"].get("fails", 0))
            total_fail = int(metrics["checks"].get("fails", 0))
        elif "http_reqs" in metrics or "http_req_failed" in metrics:
            total_req = int(metrics.get("http_reqs", {}).get("count", 0))
            total_fail = int(metrics.get("http_req_failed", {}).get("count", 0))
    return total_req, total_fail, per_method

def _duration_seconds(data: Dict[str, Any]) -> float:
    it = data.get("metrics", {}).get("iterations", {})
    count = it.get("count")
    rate = it.get("rate")
    if count and rate and rate != 0:
        return float(count) / float(rate)
    return 0.0

def build_summary_from_k6(json_bytes: bytes) -> Tuple[Summary, Dict[str, bool]]:
    data = json.loads(json_bytes.decode("utf-8", errors="strict"))
    metrics: Dict[str, Any] = data.get("metrics", {})
    total_req, total_fail, per_method = _extract_counts(data)
    error_rate = round(total_fail / max(total_req, 1), 4)
    duration_s = _duration_seconds(data)
    duration_ms = int(duration_s * 1000.0)
    throughput = (total_req / duration_s) if duration_s else 0.0

    if "grpc_req_duration" in metrics:
        lat = _latency_from_metric_dict(metrics["grpc_req_duration"])
    elif "http_req_duration" in metrics:
        lat = _latency_from_metric_dict(metrics["http_req_duration"])
    else:
        lat = Latency()

    flags = {
        "approximated_percentiles": (lat.p99 == 0.0),
        "approximated_duration": (duration_ms == 0),
        "count_source": "root_group.checks" if per_method else ("metrics.checks" if "checks" in metrics else "http_reqs"),
    }

    overall = OverallMetrics(
        name="(overall)", requests=total_req, failures=total_fail, error_rate=error_rate,
        duration_ms=duration_ms, throughput_rps=throughput, latency_ms=lat
    )

    by_method: List[MethodMetrics] = []
    for method_name, cnt in sorted(per_method.items()):
        req = int(cnt.get("requests", 0))
        fai = int(cnt.get("failures", 0))
        er = round(fai / max(req, 1), 4)
        thr = (req / duration_s) if duration_s else 0.0
        mkey = _method_metric_key(method_name)
        mlat = _latency_from_metric_dict(metrics.get(mkey, {}))
        by_method.append(MethodMetrics(
            name=method_name, requests=req, failures=fai, error_rate=er,
            duration_ms=duration_ms, throughput_rps=thr, latency_ms=mlat
        ))

    run_id = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return Summary(tool="k6", run_id=run_id, overall=overall, by_method=by_method), flags