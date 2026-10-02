#!/usr/bin/env python3
"""Builds demo/guide.xml: a TV guide for the demo playlist's channels.

The demo channels are not real broadcasters, so their schedule is generated
here: each channel rotates through Blender Foundation open movies, from
yesterday to six days ahead. Run daily by .github/workflows/demo-guide.yml so
the guide always covers the current week.
"""
import datetime as dt
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CREDIT = "Blender Foundation open movie"
FILMS = {
    "tos": ("Tears of Steel", "Sci-Fi", "In a future Amsterdam, scientists try to save the world from robots by restaging a painful break-up.", "CC BY 3.0"),
    "sintel": ("Sintel", "Fantasy", "A young woman crosses a harsh land to find the baby dragon she once rescued.", "CC BY 3.0"),
    "bbb": ("Big Buck Bunny", "Animation", "A gentle giant of a rabbit gets even with three rodents who bully the forest's smaller animals.", "CC BY 3.0"),
    "ed": ("Elephants Dream", "Sci-Fi", "Two men explore a vast, strange machine that may exist only in one of their minds.", "CC BY 3.0"),
    "cosmos": ("Cosmos Laundromat", "Animation", "On a lonely island, Franck the sheep meets a salesman who offers him any life he wants.", "CC BY 4.0"),
    "agent": ("Agent 327: Operation Barbershop", "Animation", "Agent 327 goes undercover in a barbershop to find a missing colleague.", "CC BY-ND 4.0"),
    "cam1": ("Caminandes: Llama Drama", "Kids", "Koro the llama tries to cross a road to reach the grass on the other side.", "CC BY 3.0"),
    "cam2": ("Caminandes: Gran Dillama", "Kids", "Koro wants the juicy leaves on the far side of an electric fence.", "CC BY 3.0"),
    "cam3": ("Caminandes: Llamigos", "Kids", "In the depths of winter, Koro meets Oti the penguin and they compete for the last berries.", "CC BY 3.0"),
}

# tvg-id -> (display name, rotation of films)
CHANNELS = {
    "StudioOne.demo": ("Studio One", ["tos", "cosmos", "sintel", "ed", "agent"]),
    "Fable.demo": ("Fable", ["sintel", "ed", "tos", "cosmos"]),
    "BunnyKids.demo": ("Bunny Kids", ["bbb", "cam1", "cam2", "cam3"]),
    "LlamaTV.demo": ("Llama TV", ["cam1", "cam2", "cam3", "bbb"]),
    "Nova.demo": ("Nova", ["cosmos", "tos", "agent", "sintel"]),
    "Agent247.demo": ("Agent 24/7", ["agent", "bbb", "cosmos", "cam2"]),
    "Reverie.demo": ("Reverie", ["ed", "sintel", "cosmos", "tos"]),
}

# Slot lengths in minutes, cycled so the guide grid isn't uniform
SLOTS = [30, 60, 30, 30, 60, 30]
DAYS_BACK = 1
DAYS_AHEAD = 6
SCHEDULE_EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
OUTPUT = Path(__file__).with_name("guide.xml")


def xmltv_time(moment: dt.datetime) -> str:
    return moment.strftime("%Y%m%d%H%M%S +0000")


def main() -> int:
    today = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - dt.timedelta(days=DAYS_BACK)
    end = today + dt.timedelta(days=DAYS_AHEAD + 1)

    guide = ET.Element("tv", {"generator-info-name": "JamRun demo guide"})
    for tvg_id, (name, _) in CHANNELS.items():
        channel = ET.SubElement(guide, "channel", {"id": tvg_id})
        ET.SubElement(channel, "display-name").text = name

    total = 0
    for offset, (tvg_id, (_, rotation)) in enumerate(CHANNELS.items()):
        # Walk the rotation from a fixed date so each slot keeps its programme between refreshes
        moment = SCHEDULE_EPOCH
        step = offset * 3
        while moment < end:
            film = FILMS[rotation[step % len(rotation)]]
            minutes = SLOTS[(step + offset) % len(SLOTS)]
            stop = moment + dt.timedelta(minutes=minutes)
            if stop <= start:
                moment = stop
                step += 1
                continue
            programme = ET.SubElement(guide, "programme", {
                "start": xmltv_time(moment), "stop": xmltv_time(stop), "channel": tvg_id,
            })
            title, category, summary, licence = film
            ET.SubElement(programme, "title", {"lang": "en"}).text = title
            ET.SubElement(programme, "desc", {"lang": "en"}).text = f"{summary} {CREDIT}, {licence}."
            ET.SubElement(programme, "category", {"lang": "en"}).text = category
            moment = stop
            step += 1
            total += 1

    ET.indent(guide)
    ET.ElementTree(guide).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {total} programmes for {len(CHANNELS)} channels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
