"""Shazam a long DJ mix by recognizing short clips at regular intervals.

Usage: python scan.py <audio-file> [step_seconds] [clip_seconds]
"""
import asyncio, json, subprocess, sys, tempfile, os
from shazamio import Shazam

def ts(s):
    return f"{int(s)//3600:d}:{int(s)%3600//60:02d}:{int(s)%60:02d}"

def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", path])
    return float(out)

def clip(path, start, length, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(length), "-i", path,
                    "-ac", "1", "-ar", "16000", dst], check=True)

async def main():
    path = sys.argv[1]
    step = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    length = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    offset = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    shazam = Shazam()
    total = duration(path)
    hits = []
    with tempfile.TemporaryDirectory() as tmp:
        for start in range(offset, int(total) - length, step):
            dst = os.path.join(tmp, "c.wav")
            clip(path, start, length, dst)
            for attempt in range(3):
                try:
                    r = await shazam.recognize(dst)
                    break
                except Exception as e:
                    r = {}
                    await asyncio.sleep(5 * (attempt + 1))
            t = r.get("track")
            if t:
                hits.append({"t": start, "artist": t.get("subtitle"), "title": t.get("title"),
                             "url": t.get("url")})
                print(f"{ts(start)}  {t.get('subtitle')} - {t.get('title')}", flush=True)
            else:
                print(f"{ts(start)}  --", flush=True)
            await asyncio.sleep(0.5)
    json.dump(hits, sys.stdout if False else open(path + ".hits.json", "w"), indent=1)

asyncio.run(main())
