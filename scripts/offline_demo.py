"""Demonstrate only an unrendered episode plan (no AI accounts used)."""
import json
from studio.planning import build_example_episode, summarize_plan


def main() -> None:
    example = build_example_episode()
    print(json.dumps(summarize_plan(example), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
