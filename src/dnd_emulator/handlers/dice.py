"""Dice rolling handler for WebSocket events."""

import logging
import random
from typing import Any

from flask_socketio import emit

logger = logging.getLogger(__name__)


def handle_dice_roll(data: dict[str, Any]) -> None:
    """Handle dice roll requests."""
    notation = data.get("notation", "1d20")

    # Parse dice notation (simplified)
    try:
        parts = notation.lower().split("d")
        num_dice = int(parts[0])

        if "+" in parts[1]:
            die_parts = parts[1].split("+")
            die_size = int(die_parts[0])
            modifier = int(die_parts[1])
        elif "-" in parts[1]:
            die_parts = parts[1].split("-")
            die_size = int(die_parts[0])
            modifier = -int(die_parts[1])
        else:
            die_size = int(parts[1])
            modifier = 0

        # Roll dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]  # noqa: S311
        total = sum(rolls) + modifier

        emit(
            "dice_result",
            {
                "notation": notation,
                "rolls": rolls,
                "modifier": modifier,
                "total": total,
            },
        )

    except (ValueError, IndexError) as e:
        emit("error", {"message": f"Invalid dice notation: {e!s}"})
