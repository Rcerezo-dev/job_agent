import argparse

_DEFAULT_GOAL = (
    "Find the best AI/ML engineering jobs in Madrid today and prepare "
    "application documents for the top match."
)


def main():
    parser = argparse.ArgumentParser(description="Job search agent")
    parser.add_argument(
        "--manual", action="store_true",
        help="Use the manual interactive pipeline instead of the agent",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Skip human confirmation prompts (agent mode only)",
    )
    parser.add_argument(
        "--goal", default=_DEFAULT_GOAL,
        help="What the agent should accomplish (agent mode only)",
    )
    args = parser.parse_args()

    if args.manual:
        from pipeline import run_pipeline
        run_pipeline()
    else:
        from agent import run
        run(args.goal, auto=args.auto)


if __name__ == "__main__":
    main()
