"""
OSINT Military Movement Tracker
--------------------------------
Correlates public signals from multiple open data sources
to detect and visualize patterns of geopolitical activity.

Usage:
    python main.py --region iran --days 7
    python main.py --region iran --days 1 --output terminal
    python main.py --list-regions
"""

import asyncio
import click
import yaml
import logging
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from src.collectors.internet_collector import InternetCollector
from src.collectors.conflict_collector import ConflictCollector
from src.collectors.news_collector import NewsCollector
from src.collectors.aircraft_collector import AircraftCollector
from src.analyzers.signal_correlator import SignalCorrelator
from src.analyzers.anomaly_detector import AnomalyDetector
from src.analyzers.pattern_scorer import PatternScorer
from src.visualizers.dashboard import Dashboard
from src.visualizers.map_renderer import MapRenderer

console = Console()

def load_config() -> dict:
    config_path = Path("config/regions.yaml")
    with open(config_path) as f:
        return yaml.safe_load(f)


def setup_logging(log_level: str):
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def run_pipeline(region_name: str, days: int, output: str, config: dict, demo_mode: bool = False):
    """Main async pipeline — collects, correlates, scores, and visualizes."""

    region = config["regions"].get(region_name)
    if not region:
        console.print(f"[red]❌ Region '{region_name}' not found in config/regions.yaml[/red]")
        raise SystemExit(1)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    demo_marker = " [DEMO MODE]" if demo_mode else ""
    console.print(Panel(
        f"[bold cyan]🛰️  OSINT TRACKER{demo_marker}[/bold cyan]\n"
        f"Region: [yellow]{region['name']}[/yellow]  |  "
        f"Period: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}",
        border_style="cyan" if not demo_mode else "yellow"
    ))

    # ── COLLECTION PHASE ──────────────────────────────────
    console.print("\n[bold]📡 Collecting signals from public sources...[/bold]")

    collectors = [
        InternetCollector(region, start_date, end_date, demo_mode=demo_mode),
        ConflictCollector(region, start_date, end_date, demo_mode=demo_mode),
        NewsCollector(region, start_date, end_date, demo_mode=demo_mode),
        AircraftCollector(region, start_date, end_date, demo_mode=demo_mode),
    ]

    results = {}
    for collector in collectors:
        with console.status(f"  Fetching {collector.name}..."):
            try:
                data = await collector.collect()
                results[collector.source_key] = data
                console.print(f"  [green]✓[/green] {collector.name}: {collector.summary()}")
            except Exception as e:
                console.print(f"  [yellow]⚠[/yellow] {collector.name}: {e} (skipping)")
                results[collector.source_key] = None

    # ── ANALYSIS PHASE ─────────────────────────────────────
    console.print("\n[bold]🔍 Analysing signals...[/bold]")

    correlator = SignalCorrelator(results, config["thresholds"])
    correlated = correlator.correlate()

    detector = AnomalyDetector(correlated, config["thresholds"])
    anomalies = detector.detect()

    scorer = PatternScorer(anomalies, config["scoring_weights"])
    scores = scorer.score()

    # ── OUTPUT PHASE ───────────────────────────────────────
    dashboard = Dashboard(region, scores, anomalies, start_date, end_date)
    dashboard.render()

    if output in ("html", "both"):
        renderer = MapRenderer(region, results, scores, anomalies)
        output_path = renderer.render()
        console.print(f"\n[green]🗺️  Map saved to:[/green] {output_path}")

    return scores


@click.command()
@click.option("--region", "-r", default="iran",
              help="Region to analyse (see config/regions.yaml)")
@click.option("--days", "-d", default=7, type=int,
              help="Number of days to look back")
@click.option("--output", "-o",
              type=click.Choice(["terminal", "html", "both"]),
              default="both",
              help="Output format")
@click.option("--demo", is_flag=True,
              help="Use demo/cached data (no API keys required)")
@click.option("--list-regions", is_flag=True,
              help="List all available regions and exit")
@click.option("--log-level", default="WARNING",
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
              help="Logging verbosity")
def main(region, days, output, demo, list_regions, log_level):
    """
    🛰️  OSINT Military Movement Tracker

    Correlates public signals (internet outages, conflict events,
    news volume, aircraft patterns) to detect geopolitical activity.

    All data sources are publicly available and legally accessible.

    Examples:
      python main.py --region iran --demo              # Demo mode, no API keys
      python main.py --region iran --days 7            # Real data (needs API keys)
      python main.py --list-regions                    # Show available regions
    """
    setup_logging(log_level)
    config = load_config()

    if list_regions:
        console.print("\n[bold cyan]Available regions:[/bold cyan]")
        for key, val in config["regions"].items():
            console.print(f"  [yellow]{key}[/yellow] — {val['name']}")
        return

    scores = asyncio.run(run_pipeline(region, days, output, config, demo_mode=demo))

    # Exit code reflects severity — useful in CI/scripting contexts
    composite = scores.get("composite", 0)
    if composite >= 7.0:
        raise SystemExit(2)   # High activity
    elif composite >= 4.0:
        raise SystemExit(1)   # Moderate activity
    else:
        raise SystemExit(0)   # Normal


if __name__ == "__main__":
    main()
