from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional

from config import Config


@dataclass
class MealPlanState:
    active: bool
    target_count: int
    planned_meals: list[str] = field(default_factory=list)
    rejected_meals: list[str] = field(default_factory=list)
    started_at: str = ""
    last_updated: str = ""

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> Optional[MealPlanState]:
        """Return current state from disk, or None if no file exists."""
        path = Config.MEAL_PLAN_STATE_FILE
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return cls(**data)
        except Exception:
            return None

    def save(self) -> None:
        self.last_updated = datetime.now().isoformat()
        with open(Config.MEAL_PLAN_STATE_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def clear(self) -> None:
        path = Config.MEAL_PLAN_STATE_FILE
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def is_complete(self) -> bool:
        return len(self.planned_meals) >= self.target_count

    def summary(self) -> str:
        remaining = self.target_count - len(self.planned_meals)
        lines = [
            f"Meal planning in progress: {len(self.planned_meals)}/{self.target_count} meals validated.",
            f"Planned: {self.planned_meals or 'none yet'}.",
            f"Rejected: {self.rejected_meals or 'none'}.",
            f"Remaining: {remaining} meal(s) to choose.",
        ]
        return " ".join(lines)
