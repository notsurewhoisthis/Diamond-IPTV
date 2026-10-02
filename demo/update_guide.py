#!/usr/bin/env python3
"""Builds demo/guide.xml: the TV guide for the demo playlist's live channels.

Pulls the free epg.pw XMLTV feeds, keeps only the channels in CHANNELS and
renames them to the tvg-id values used in jamrun-demo.m3u. Run daily by
.github/workflows/demo-guide.yml so the guide never runs out.
"""
import gzip
import io
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

FEEDS = {
    "GB": "https://epg.pw/xmltv/epg_GB.xml.gz",
    "US": "https://epg.pw/xmltv/epg_US.xml.gz",
}

# tvg-id in the playlist -> (feed, epg.pw channel id, display name)
CHANNELS = {
    "France24.en": ("GB", "12048", "France 24 English"),
    "AlJazeera.en": ("GB", "12532", "Al Jazeera English"),
    "NHKWorld.en": ("GB", "12051", "NHK World-Japan"),
    "Bloomberg.eu": ("GB", "12464", "Bloomberg TV"),
    "TRTWorld.en": ("GB", "12523", "TRT World"),
    "Arirang.en": ("GB", "12037", "Arirang TV"),
    "ABCNewsLive.us": ("US", "465150", "ABC News Live"),
    "NASA.us": ("US", "561889", "NASA TV"),
}

OUTPUT = Path(__file__).with_name("guide.xml")


def fetch(url: str) -> ET.Element:
    request = urllib.request.Request(url, headers={"User-Agent": "JamRunDemoGuide/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    with gzip.open(io.BytesIO(data)) as xml:
        return ET.parse(xml).getroot()


def main() -> int:
    wanted = {(feed, source_id): tvg_id for tvg_id, (feed, source_id, _) in CHANNELS.items()}
    guide = ET.Element("tv", {"generator-info-name": "JamRun demo guide (from epg.pw)"})
    for tvg_id, (_, _, name) in CHANNELS.items():
        channel = ET.SubElement(guide, "channel", {"id": tvg_id})
        ET.SubElement(channel, "display-name").text = name

    counts = {tvg_id: 0 for tvg_id in CHANNELS}
    for feed, url in FEEDS.items():
        for programme in fetch(url).iter("programme"):
            tvg_id = wanted.get((feed, programme.get("channel")))
            if tvg_id is None:
                continue
            programme.set("channel", tvg_id)
            guide.append(programme)
            counts[tvg_id] += 1

    empty = [tvg_id for tvg_id, count in counts.items() if count == 0]
    if len(empty) == len(CHANNELS):
        print("No programmes found for any channel; keeping the previous guide.", file=sys.stderr)
        return 1
    for tvg_id in empty:
        print(f"warning: no programmes for {tvg_id}", file=sys.stderr)

    ET.indent(guide)
    ET.ElementTree(guide).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {sum(counts.values())} programmes for {len(CHANNELS) - len(empty)} channels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
