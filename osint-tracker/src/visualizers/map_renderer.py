"""
Map Renderer
─────────────
Generates an interactive HTML map using Folium.

Layers rendered:
- Conflict event heatmap (ACLED geo points)
- ISR/military aircraft positions
- Region bounding box overlay
- Composite score legend

Output: a self-contained HTML file you can open in any browser.
"""

import folium
from folium.plugins import HeatMap, MarkerCluster
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/processed")


class MapRenderer:
    def __init__(self, region: dict, results: dict, scores: dict, anomalies: dict):
        self.region = region
        self.results = results
        self.scores = scores
        self.anomalies = anomalies

    def render(self) -> str:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        center = self.region.get("center", [32.0, 53.0])
        m = folium.Map(
            location=center,
            zoom_start=6,
            tiles="CartoDB dark_matter",  # Dark theme — more dramatic
        )

        self._add_bounding_box(m)
        self._add_conflict_heatmap(m)
        self._add_conflict_markers(m)
        self._add_aircraft_markers(m)
        self._add_legend(m)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        region_slug = self.region["name"].lower().replace(" ", "_")
        output_path = OUTPUT_DIR / f"{region_slug}_{timestamp}.html"

        m.save(str(output_path))
        return str(output_path)

    def _add_bounding_box(self, m: folium.Map):
        bbox = self.region.get("bbox", [])
        if len(bbox) != 4:
            return
        min_lat, min_lon, max_lat, max_lon = bbox
        folium.Rectangle(
            bounds=[[min_lat, min_lon], [max_lat, max_lon]],
            color="#00ffff",
            weight=1,
            fill=True,
            fill_opacity=0.03,
            tooltip=f"Monitoring zone: {self.region['name']}",
        ).add_to(m)

    def _add_conflict_heatmap(self, m: folium.Map):
        geo_points = self.anomalies.get("acled", {}).get("geo_points", [])
        if not geo_points:
            return

        heat_data = [
            [pt["lat"], pt["lon"], 1 + pt.get("fatalities", 0) * 0.1]
            for pt in geo_points
            if pt.get("lat") and pt.get("lon")
        ]

        if heat_data:
            HeatMap(
                heat_data,
                name="Conflict Intensity",
                radius=25,
                blur=15,
                gradient={"0.2": "blue", "0.5": "orange", "1.0": "red"},
            ).add_to(m)

    def _add_conflict_markers(self, m: folium.Map):
        geo_points = self.anomalies.get("acled", {}).get("geo_points", [])
        if not geo_points:
            return

        cluster = MarkerCluster(name="Conflict Events").add_to(m)

        for pt in geo_points:
            lat, lon = pt.get("lat"), pt.get("lon")
            if not lat or not lon:
                continue

            color = (
                "red" if "Explosion" in pt.get("type", "") or "Battle" in pt.get("type", "")
                else "orange"
            )

            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.8,
                popup=folium.Popup(
                    f"<b>{pt.get('type', 'Unknown')}</b><br>"
                    f"📍 {pt.get('location', '?')}<br>"
                    f"📅 {pt.get('date', '?')}<br>"
                    f"💀 Fatalities: {pt.get('fatalities', 0)}<br>"
                    f"📝 {pt.get('notes', '')[:150]}",
                    max_width=300,
                ),
                tooltip=f"{pt.get('location')} — {pt.get('type')}",
            ).add_to(cluster)

    def _add_aircraft_markers(self, m: folium.Map):
        isr_aircraft = self.anomalies.get("aircraft", {}).get("isr_spotted", [])

        aircraft_layer = folium.FeatureGroup(name="ISR / Military Aircraft")

        for ac in isr_aircraft:
            lat, lon = ac.get("lat"), ac.get("lon")
            if not lat or not lon:
                continue

            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(
                    html='<div style="font-size:20px;">✈</div>',
                    icon_size=(20, 20),
                ),
                popup=folium.Popup(
                    f"<b>{ac.get('callsign', 'UNKNOWN')}</b><br>"
                    f"Type: {ac.get('type', '?')}<br>"
                    f"Mission: {ac.get('mission', 'Unknown')}<br>"
                    f"ICAO: {ac.get('hex', '?')}",
                    max_width=250,
                ),
                tooltip=f"✈ {ac.get('callsign')} ({ac.get('type')})",
            ).add_to(aircraft_layer)

        aircraft_layer.add_to(m)
        folium.LayerControl().add_to(m)

    def _add_legend(self, m: folium.Map):
        composite = self.scores.get("composite", 0)
        status = self.scores.get("status", "UNKNOWN")
        region_name = self.region["name"]

        color = "#ff4444" if composite >= 7 else "#ffaa00" if composite >= 4 else "#44ff44"

        legend_html = f"""
        <div style="
            position: fixed;
            bottom: 30px; left: 30px; z-index: 1000;
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            border: 1px solid {color};
            font-family: monospace;
            font-size: 13px;
            min-width: 240px;
        ">
            <div style="font-size:15px; font-weight:bold; color:{color}; margin-bottom:8px;">
                🛰️ OSINT TRACKER
            </div>
            <div>Region: <b>{region_name}</b></div>
            <div>Composite Score: <b style="color:{color}">{composite:.1f} / 10</b></div>
            <div style="margin-top:6px; color:{color}; font-weight:bold">{status}</div>
            <hr style="border-color:#444; margin:8px 0">
            <div style="font-size:11px; color:#aaa;">
                🔴 Red markers = Explosions/Battles<br>
                🟠 Orange markers = Other conflict events<br>
                ✈ Aircraft = ISR / Military flights<br>
                Heatmap = Conflict intensity
            </div>
            <div style="font-size:10px; color:#666; margin-top:8px;">
                Data: ACLED · IODA · ADS-B Exchange · NewsAPI<br>
                Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
