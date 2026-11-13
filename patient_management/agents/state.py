"""Serializable state used while an appointment concierge run is executing."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppointmentAgentState:
    goal: str
    steps: list[dict] = field(default_factory=list)

    def record(self, tool: str, **details) -> None:
        self.steps.append({"tool": tool, **details})
