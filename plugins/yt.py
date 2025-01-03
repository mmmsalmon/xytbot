import yt_dlp
import yt_dlp.utils
from numerize.numerize import numerize


def yt_link_preview(video_id: str) -> str:
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url=url, download=False)
        day = info["upload_date"]
        data = [
            f"*{info['title']}*",
            f"{info['description'][:80].strip()}...",
            f"🎥{info['channel']}",
            f"👁️{numerize(info['view_count'])}",
            f"⏳{info['duration_string']}",
            f"👍🏻{numerize(info['like_count'])}",
            f"🗓️{day[:4]}-{day[4:6:]}-{day[6:]}",
        ]
        return f"{data[0]}\n{data[1]}\n{' '.join(data[2:])}"
    except yt_dlp.utils.DownloadError:
        return "error"
