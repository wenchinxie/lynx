"""CLI commands for lynx."""

import json
from pathlib import Path

import click

import lynx
from lynx.exceptions import RunNotFoundError
from lynx.storage import sqlite


@click.group()
@click.version_option(version=lynx.__version__, prog_name="lynx")
def cli():
    """Lynx - Local backtest tracking for quantitative analysts.

    Track, compare, and analyze your backtest runs.
    """
    pass


@cli.command()
@click.option("--port", default=8501, help="Port number for the web server")
def serve(port: int):
    """Launch the web dashboard.

    Example:
        lynx serve
        lynx serve --port 8080
    """
    click.echo(f"Starting Lynx dashboard at http://localhost:{port}")
    from lynx.dashboard import launch_dashboard
    launch_dashboard(port=port, open_browser=True)


@cli.command("list")
@click.option("--strategy", "-s", default=None, help="Filter by strategy name")
@click.option("--limit", "-n", default=None, type=int, help="Maximum number of runs to show")
def list_runs(strategy: str | None, limit: int | None):
    """List all runs.

    Example:
        lynx list
        lynx list --strategy momentum
        lynx list --limit 10
    """
    sqlite.init_db()

    runs = lynx.runs(strategy=strategy, limit=limit)

    if not runs:
        click.echo("No runs found.")
        return

    # Print header
    click.echo(f"{'ID':<50} {'Strategy':<20} {'Sharpe':<8} {'Return':<10} {'Created'}")
    click.echo("-" * 100)

    for run in runs:
        sharpe = run.metrics.get("sharpe_ratio", 0)
        ret = run.metrics.get("total_return", 0)
        created = run.created_at.strftime("%Y-%m-%d %H:%M")

        click.echo(
            f"{run.id:<50} "
            f"{run.strategy_name:<20} "
            f"{sharpe:>7.2f} "
            f"{ret:>9.1%} "
            f"{created}"
        )


@cli.command()
@click.argument("run_id")
def show(run_id: str):
    """Show details for a specific run.

    Example:
        lynx show margin_transactions_20241214_153042_a7b2
    """
    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError:
        click.echo(f"Error: Run '{run_id}' not found.", err=True)
        raise SystemExit(1) from None

    click.echo(f"\n{'='*60}")
    click.echo(f"Run: {run.id}")
    click.echo(f"{'='*60}\n")

    click.echo(f"Strategy: {run.strategy_name}")
    click.echo(f"Created:  {run.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

    if run.params:
        click.echo("\nParameters:")
        for key, value in run.params.items():
            click.echo(f"  {key}: {value}")

    click.echo("\nMetrics:")
    metric_labels = {
        "total_return": "Total Return",
        "annualized_return": "Annualized Return",
        "sharpe_ratio": "Sharpe Ratio",
        "max_drawdown": "Max Drawdown",
        "win_rate": "Win Rate",
        "profit_factor": "Profit Factor",
        "num_trades": "Number of Trades",
        "avg_trade_duration_days": "Avg Trade Duration (days)",
    }

    for key, label in metric_labels.items():
        value = run.metrics.get(key, "N/A")
        if isinstance(value, float):
            if key in ["total_return", "annualized_return", "max_drawdown", "win_rate"]:
                click.echo(f"  {label}: {value:.2%}")
            else:
                click.echo(f"  {label}: {value:.2f}")
        else:
            click.echo(f"  {label}: {value}")

    artifacts = run.list_artifacts()
    click.echo(f"\nArtifacts: {', '.join(artifacts)}")


@cli.command()
@click.argument("run_id")
@click.confirmation_option(prompt="Are you sure you want to delete this run?")
def delete(run_id: str):
    """Delete a run and its artifacts.

    Example:
        lynx delete margin_transactions_20241214_153042_a7b2
    """
    sqlite.init_db()

    try:
        lynx.delete(run_id)
        click.echo(f"Run '{run_id}' deleted successfully.")
    except RunNotFoundError:
        click.echo(f"Error: Run '{run_id}' not found.", err=True)
        raise SystemExit(1) from None


@cli.command()
@click.argument("run_id")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output directory")
def export(run_id: str, output: str):
    """Export a run to a directory.

    Exports trades and all artifacts as CSV files.

    Example:
        lynx export margin_transactions_20241214_153042_a7b2 --output ./export/
    """
    sqlite.init_db()

    try:
        run = lynx.load(run_id)
    except RunNotFoundError:
        click.echo(f"Error: Run '{run_id}' not found.", err=True)
        raise SystemExit(1) from None

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export metadata
    metadata = {
        "id": run.id,
        "strategy_name": run.strategy_name,
        "created_at": run.created_at.isoformat(),
        "params": run.params,
        "metrics": run.metrics,
    }

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    click.echo(f"Exported: {metadata_path}")

    # Export trades
    trades = run.get_trades()
    trades_path = output_dir / "trades.csv"
    trades.to_csv(trades_path, index=False)
    click.echo(f"Exported: {trades_path}")

    # Export other artifacts
    artifacts = run.list_artifacts()
    for artifact_name in artifacts:
        if artifact_name == "trades":
            continue

        try:
            df = run.get_signal(artifact_name)
        except Exception:
            try:
                df = run.get_data(artifact_name)
            except Exception:
                continue

        artifact_path = output_dir / f"{artifact_name}.csv"
        df.to_csv(artifact_path)
        click.echo(f"Exported: {artifact_path}")

    click.echo(f"\nExport complete: {output_dir}")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
