"""
Terminal Dashboard
───────────────────
Renders a clean, colour-coded signal report using the Rich library.
"""

from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

console = Console()


class Dashboard:
    def __init__(self, region: dict, scores: dict, anomalies: dict,
                 start_date: datetime, end_date: datetime):
        self.region = region
        self.scores = scores
        self.anomalies = anomalies
        self.start_date = start_date
        self.end_date = end_date

    def render(self):
        console.print()
        self._render_header()
        self._render_signal_table()
        self._render_composite()
        self._render_hotspots()
        self._render_isr_aircraft()

    def _render_header(self):
        console.rule(f"[bold cyan]OSINT TRACKER — {self.region['name'].upper()}[/bold cyan]")
        console.print(
            f"  Period: [yellow]{self.start_date.strftime('%Y-%m-%d')}[/yellow] "
            f"→ [yellow]{self.end_date.strftime('%Y-%m-%d')}[/yellow]"
            f"   Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        )
        console.print()

    def _render_signal_table(self):
        table = Table(
            title="Signal Analysis",
            box=box.ROUNDED,
            border_style="cyan",
            show_header=True,
            header_style="bold white",
        )

        table.add_column("Layer", style="bold", width=20)
        table.add_column("Score", justify="center", width=10)
        table.add_column("Severity", justify="center", width=12)
        table.add_column("Description", width=50)

        signal_map = {
            "internet": ("✈ Internet",   "internet"),
            "acled":    ("📡 Conflict",   "acled"),
            "news":     ("📰 News",       "news"),
            "aircraft": ("✈ Aircraft",   "aircraft"),
        }

        for key, (label, akey) in signal_map.items():
            score = self.scores.get(key, 0)
            anomaly = self.anomalies.get(akey, {})
            severity = anomaly.get("severity", "NORMAL")
            description = anomaly.get("description", "—")

            severity_color = {
                "CRITICAL": "red",
                "HIGH": "orange3",
                "MODERATE": "yellow",
                "NORMAL": "green",
            }.get(severity, "white")

            bar = self._bar(score)
            table.add_row(
                label,
                f"[bold]{score:.1f}[/bold]/10",
                f"[{severity_color}]{severity}[/{severity_color}]",
                description,
            )

        console.print(table)

    def _render_composite(self):
        composite = self.scores.get("composite", 0)
        status = self.scores.get("status", "UNKNOWN")
        bar = self._bar(composite, width=40)

        console.print()
        console.print(Panel(
            f"  Composite Score: [bold white]{composite:.1f}[/bold white] / 10\n"
            f"  {bar}\n"
            f"  Status: [bold]{status}[/bold]",
            title="[bold]Overall Assessment[/bold]",
            border_style="red" if composite >= 7 else "yellow" if composite >= 4 else "green",
        ))

    def _render_hotspots(self):
        hotspots = self.anomalies.get("acled", {}).get("hotspots", [])
        if not hotspots:
            return

        console.print("\n[bold]📍 Conflict Hotspots (ACLED)[/bold]")
        for i, h in enumerate(hotspots[:5], 1):
            console.print(f"  {i}. {h['location']} — {h['count']} events")

    def _render_isr_aircraft(self):
        isr = self.anomalies.get("aircraft", {}).get("isr_spotted", [])
        if not isr:
            return

        console.print("\n[bold]✈ ISR / Intelligence Aircraft Spotted[/bold]")
        for ac in isr[:5]:
            console.print(
                f"  [{ac.get('callsign', 'UNKNOWN')}] "
                f"{ac.get('type', '?')} — {ac.get('mission', 'Unknown mission')}"
            )

    def _bar(self, score: float, width: int = 20) -> str:
        filled = int((score / 10.0) * width)
        empty = width - filled
        color = "red" if score >= 7 else "yellow" if score >= 4 else "green"
        return f"[{color}]{'█' * filled}[/{color}]{'░' * empty}"
