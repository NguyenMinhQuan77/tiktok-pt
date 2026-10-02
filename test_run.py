import asyncio
import os
import shutil
from reup_processor import process_video

def cb(msg):
    # Tránh in lỗi Unicode trên Windows console
    try: print("[LOG]", msg.encode('utf-8').decode('utf-8'))
    except: pass

async def main():
    url = "https://www.tiktok.com/@englishbyjay/video/7685282263554133266"
    out_folder = r"C:\tiktok\video"
    os.makedirs(out_folder, exist_ok=True)
    print("Starting video processing (Full: Subtitles + Voiceover)...")
    try:
        final_file = await process_video(url, use_voiceover=True, use_subtitles=True, status_callback=cb)
        dest_file = os.path.join(out_folder, "test_subtitles_only.mp4")
        if os.path.exists(dest_file):
            os.remove(dest_file)
        shutil.move(final_file, dest_file)
        print("THÀNH CÔNG! Video đã lưu tại:", dest_file)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(main())
