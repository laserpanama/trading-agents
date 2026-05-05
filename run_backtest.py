"""
run_backtest.py – CLI entry point for running a backtest from the terminal.

Usage:
    python run_backtest.py
    python run_backtest.py --symbol TSLA --start 2024-01-01 --end 2024-06-30
    python run_backtest.py --symbol NVDA --start 2024-01-01 --end 2024-03-31 --capital 50000 --rounds 3
"""
import argparse
import json

from backtest import Backtest


def main() -> None:
    parser = argparse.ArgumentParser(description="TradingAgents CLI Backtest Runner")
    parser.add_argument("--symbol", default="AAPL", help="Stock ticker symbol (default: AAPL)")
    parser.add_argument("--start", default="2024-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2024-03-29", help="End date YYYY-MM-DD")
    parser.add_argument("--capital", type=float, default=100_000.0, help="Initial capital in USD")
    parser.add_argument("--rounds", type=int, default=2, help="Bull/bear debate rounds per day")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose agent output")
    args = parser.parse_args()

    print("\n[TradingAgents Backtest]")
    print(f"   Symbol : {args.symbol}")
    print(f"   Period : {args.start} -> {args.end}")
    print(f"   Capital: ${args.capital:,.0f}")
    print(f"   Rounds : {args.rounds}\n")

    bt = Backtest(
        symbol=args.symbol,
        start_date=args.start,
        end_date=args.end,
        initial_capital=args.capital,
        debate_rounds=args.rounds,
        verbose=not args.quiet,
    )
    bt.run()
    metrics = bt.metrics()

    print("\n" + "=" * 50)
    print("  PERFORMANCE METRICS")
    print("=" * 50)
    for k, v in metrics.items():
        print(f"  {k:<30} {v}")
    print("=" * 50)
    print(f"  Trades executed: {len(bt.trades)}")

    if bt.trades:
        print("\n  Trade Log:")
        for t in bt.trades:
            print(f"    {t[0]}  {t[1]:4s}  {t[2]:.4f} shares @ ${t[3]:.2f}")


if __name__ == "__main__":
    main()
