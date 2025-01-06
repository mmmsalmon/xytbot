import yt_dlp
import yt_dlp.utils
from numerize.numerize import numerize


def yt_link_preview(video_id: str) -> str:
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url=url, download=False)
        day = info["upload_date"]
        if "duration_string" not in info:
            info["duration_string"] = "LIVE"
        like_count = "(hidden)"
        if info["like_count"]:  # handle null like_count
            like_count = numerize(info["like_count"])
        data = [
            f"*{info['title']}*",
            f"{info['description'][:80].strip()}...",
            f"🎥{info['channel']}",
            f"👁️{numerize(info['view_count'])}",
            f"⏳{info['duration_string']}",
            f"👍🏻{like_count}",
            f"🗓️{day[:4]}-{day[4:6:]}-{day[6:]}",
        ]
        return f"{data[0]}\n{data[1]}\n{' '.join(data[2:])}"
    except yt_dlp.utils.DownloadError as e:
        e = str(e)
        if "Sign in to confirm your age" in e:
            err = "error: age restricted video"
        elif "Video unavailable" in e or "Incomplete YouTube ID" in e:
            err = "error: malformed video ID"
        else:
            err = "error"
        return err


def x_link_preview(url) -> str:
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url=url, download=False)
        data = [
            f"*{info['uploader']}*",
            f"{info['description']}",
        ]
        return f"{data[0]}\n{data[1]}"
    except yt_dlp.utils.DownloadError:
        return None


if __name__ == "__main__":  # test
    print(yt_link_preview("bv__9O5CZok"))
