from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Latency(BaseModel):
    p50: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0

class MethodMetrics(BaseModel):
    name: str
    requests: int
    failures: int
    error_rate: float
    duration_ms: int
    throughput_rps: float
    latency_ms: Latency

class OverallMetrics(MethodMetrics):
    name: str = "(overall)"

class Summary(BaseModel):
    tool: str
    run_id: str
    overall: OverallMetrics
    by_method: List[MethodMetrics] = Field(default_factory=list)

class AIReport(BaseModel):
    title: str
    overview: str
    key_metrics: Dict[str, float] = Field(default_factory=dict)
    highlights: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: Optional[str] = None

class AnalyzeResponse(BaseModel):
    summary: Summary
    ai_report: AIReport
    token_usage: TokenUsage
    metadata: Dict[str, Any] = Field(default_factory=dict)