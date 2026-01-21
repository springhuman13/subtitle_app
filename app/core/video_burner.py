import subprocess
import os
from pathlib import Path


def burn(video_path, srt_path, output_path):
    video_path = Path(video_path).resolve()
    srt_path = Path(srt_path).resolve()
    output_path = Path(output_path).resolve()

    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vf", f"subtitles='{srt_escaped}'",
        "-c:a", "copy",
        str(output_path),
    ]

    subprocess.run(cmd, check=True)
