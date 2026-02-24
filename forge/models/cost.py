from __future__ import annotations

from dataclasses import dataclass, field

COST_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "o1": (15.00, 60.00),
    "o3-mini": (1.10, 4.40),
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "claude-opus-4-20250514": (15.00, 75.00),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.00),
    "deepseek-chat": (0.14, 0.28),
    "deepseek-reasoner": (0.55, 2.19),
    "default_local": (0.0, 0.0),
}


@dataclass
class CostRecord:
    model: str
    tokens_in: int
    tokens_out: int
    cost: float
    session_id: str = ""


@dataclass
class CostTracker:
    records: list[CostRecord] = field(default_factory=list)
    total_cost: float = 0.0
    total_tokens_in: int = 0
    total_tokens_out: int = 0

    def track(self, model: str, tokens_in: int, tokens_out: int, cost: float, session_id: str = "") -> None:
        if cost == 0.0:
            cost = self.estimate_cost(model, tokens_in, tokens_out)

        record = CostRecord(
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost=cost,
            session_id=session_id,
        )
        self.records.append(record)
        self.total_cost += cost
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out

    def estimate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        rates = COST_TABLE.get(model, COST_TABLE.get("default_local", (0.0, 0.0)))
        input_cost = (tokens_in / 1_000_000) * rates[0]
        output_cost = (tokens_out / 1_000_000) * rates[1]
        return input_cost + output_cost

    def get_summary(self) -> dict:
        by_model: dict[str, dict] = {}
        for record in self.records:
            if record.model not in by_model:
                by_model[record.model] = {"cost": 0.0, "tokens_in": 0, "tokens_out": 0, "calls": 0}
            by_model[record.model]["cost"] += record.cost
            by_model[record.model]["tokens_in"] += record.tokens_in
            by_model[record.model]["tokens_out"] += record.tokens_out
            by_model[record.model]["calls"] += 1

        return {
            "total_cost": self.total_cost,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_calls": len(self.records),
            "by_model": by_model,
        }
