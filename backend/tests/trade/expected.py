"""Fixture coverage that is still missing. This is about which situations the saves exercise, not about correctness:
every stage and the end-to-end chain must reproduce every save (tests/trade/test_stages.py, test_chain.py).
"""

# Edge cases no fixture exhibits yet (strict: must equal the real uncovered set; shrink it by adding fixtures).
KNOWN_UNCOVERED: frozenset[str] = frozenset(
    {"EC-N07", "EC-N09", "EC-W02"} | {f"IV-{i:02d}" for i in range(1, 17)}
)
