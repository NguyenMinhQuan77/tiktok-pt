import os
import asyncio
import yt_dlp
import whisper
from deep_translator import GoogleTranslator
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip
import datetime
import requests
import imageio_ffmpeg

# --- TỰ ĐỘNG FIX LỖI FFMPEG ---
# Thêm thư mục hiện tại (chứa ffmpeg.exe) vào PATH của hệ thống để Whisper gọi được
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["PATH"] = current_dir + os.pathsep + os.environ.get("PATH", "")

def download_video(url, output_filename, callback=None):
    if "tiktok.com" in url:
        if callback: callback(f"Đang tải video TikTok qua API chuyên dụng (Vượt Bot)...")
        try:
            api_url = 'https://www.tikwm.com/api/'
            response = requests.post(api_url, data={'url': url}).json()
            if 'data' in response and 'play' in response['data']:
                video_url = response['data']['play']
                vid_data = requests.get(video_url).content
                with open(output_filename, 'wb') as f:
                    f.write(vid_data)
                return output_filename
        except Exception as e:
            if callback: callback(f"API TikTok lỗi ({e}), chuyển sang yt-dlp...")
    
    # Fallback cho YouTube Shorts hoặc các link khác
    if callback: callback(f"Đang tải video...")
    ydl_opts = {
        'outtmpl': output_filename,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    return output_filename

def transcribe_audio(video_path, callback=None):
    if callback: callback("Đang nhận diện giọng nói (AI Whisper - Bản Base siêu tốc)...")
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result['text'], result.get('segments', [])

def my_translate(text, target_lang='vi'):
    import translators as ts
    import time
    try:
        res = ts.translate_text(text, translator='bing', from_language='auto', to_language=target_lang)
        time.sleep(0.5)
        return res
    except Exception:
        try:
            res = ts.translate_text(text, translator='google', from_language='auto', to_language=target_lang)
            time.sleep(0.5)
            return res
        except Exception:
            return text

def translate_long_text(text, target_lang='vi', callback=None):
    if callback: callback("Đang dịch toàn bộ kịch bản (giữ nguyên ngữ điệu)...")
    # Tách văn bản theo dấu chấm để giữ nguyên câu và dấu câu (rất quan trọng cho ngữ điệu)
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    translated_sentences = []
    
    # Gom các câu lại thành chunk khoảng 1000 ký tự (an toàn cho Bing API)
    current_chunk = ""
    for sentence in sentences:
        if not sentence.strip(): continue
        if len(current_chunk) + len(sentence) < 1000:
            current_chunk += sentence + ". "
        else:
            translated_sentences.append(my_translate(current_chunk.strip(), target_lang))
            current_chunk = sentence + ". "
            
    if current_chunk.strip():
        translated_sentences.append(my_translate(current_chunk.strip(), target_lang))
        
    return " ".join(translated_sentences)

async def generate_voiceover(text, output_audio, voice_name="vi-VN-HoaiMyNeural", voice_rate="+0%", voice_pitch="+0Hz", callback=None):
    if callback: callback(f"Đang lồng tiếng Việt (Edge-TTS - {voice_name}, rate={voice_rate}, pitch={voice_pitch})...")
    # Cắt nhỏ văn bản để không làm sập Edge TTS
    chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
    
    with open(output_audio, "wb") as f:
        for chunk in chunks:
            if not chunk.strip(): continue
            try:
                communicate = edge_tts.Communicate(chunk, voice_name, rate=voice_rate, pitch=voice_pitch)
                async for chunk_data in communicate.stream():
                    if chunk_data["type"] == "audio":
                        f.write(chunk_data["data"])
            except Exception as e:
                if callback: callback(f"Bỏ qua đoạn không thể đọc (có thể là emoji/nhạc): {str(e)[:50]}")
    return output_audio

def format_timestamp(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def generate_srt(segments, output_srt, callback=None):
    if callback: callback("Đang tạo và dịch Phụ đề (SRT) an toàn...")
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            translated_text = my_translate(segment['text'])
            f.write(f"{i}\n{start} --> {end}\n{translated_text}\n\n")
            import time
            time.sleep(0.1) # Rất an toàn với API trực tiếp
    return output_srt

def merge_video_audio(video_path, audio_path, output_path, use_subtitles=False, srt_path=None, sub_style="Mặc định", callback=None):
    if callback: callback("Đang render video hoàn chỉnh (Ghép âm thanh & Phụ đề)...")
    try:
        if not use_subtitles:
            video = VideoFileClip(video_path)
            new_audio = AudioFileClip(audio_path)
            final_video = video.set_audio(new_audio)
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            video.close()
            new_audio.close()
        else:
            if callback: callback("Đang nung phụ đề vào video (Hardsub) bằng FFmpeg...")
            safe_srt_path = srt_path.replace('\\', '/').replace(':', '\\:')
            
            # Xử lý các Style phụ đề khác nhau bằng force_style
            sub_filter = f"subtitles={safe_srt_path}"
            if sub_style == "Vàng Nổi Bật":
                sub_filter += ":force_style='Fontname=Arial,Fontsize=22,PrimaryColour=&H0000FFFF,Outline=2'"
            elif sub_style == "Trắng To Rõ":
                sub_filter += ":force_style='Fontname=Arial,Fontsize=26,PrimaryColour=&H00FFFFFF,Outline=3'"
            elif sub_style == "Xanh Neon":
                sub_filter += ":force_style='Fontname=Arial,Fontsize=22,PrimaryColour=&H0000FF00,Outline=2'"
            else:
                sub_filter += ":force_style='Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,Outline=1'"
                
            import subprocess
            if video_path == audio_path:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-c:v", "libx264",
                    "-vf", sub_filter,
                    "-c:a", "aac",
                    output_path
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-i", audio_path,
                    "-c:v", "libx264",
                    "-vf", sub_filter,
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    output_path
                ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
    except Exception as e:
        print(f"Lỗi render: {e}")

async def process_video(url, use_voiceover=True, use_subtitles=False, voice_name="vi-VN-HoaiMyNeural", voice_rate="+0%", voice_pitch="+0Hz", sub_style="Mặc định", status_callback=None):
    video_file = "temp_video.mp4"
    audio_file = "temp_audio.mp3"
    final_output = f"output_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"

    for file in [video_file, audio_file]:
        if os.path.exists(file):
            os.remove(file)

    try:
        download_video(url, video_file, status_callback)
        
        if not os.path.exists(video_file):
            raise Exception("Không thể tải video, TikTok đã chặn. Hãy thử một link YouTube Shorts!")
            
        original_text, segments = transcribe_audio(video_file, status_callback)
        if not original_text.strip():
            if status_callback: status_callback("Không tìm thấy âm thanh trong video để dịch!")
            return video_file

        translated_segments = []
        srt_file = "temp_subtitles.srt"
        
        if status_callback: status_callback("Đang dịch thuật nội dung từng câu an toàn...")
        with open(srt_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                trans_text = my_translate(segment['text'])
                translated_segments.append(trans_text)
                
                if use_subtitles:
                    start = format_timestamp(segment['start'])
                    end = format_timestamp(segment['end'])
                    f.write(f"{i}\n{start} --> {end}\n{trans_text}\n\n")

        if use_voiceover:
            # Dịch nguyên bản có dấu chấm, phẩy để Edge-TTS ngắt nghỉ đúng nhịp và có ngữ điệu
            full_translated_text = translate_long_text(original_text, target_lang='vi', callback=status_callback)
            if not full_translated_text.strip():
                full_translated_text = "Xin chào, video này không có tiếng."
            await generate_voiceover(full_translated_text, audio_file, voice_name, voice_rate, voice_pitch, status_callback)
            
            if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
                audio_file = video_file
                if status_callback: status_callback("Cảnh báo: Đoạn thoại chứa toàn nhạc/kí tự đặc biệt. Trả về âm thanh gốc.")
        else:
            audio_file = video_file

        merge_video_audio(
            video_path=video_file,
            audio_path=audio_file,
            output_path=final_output,
            use_subtitles=use_subtitles,
            srt_path=srt_file if use_subtitles else None,
            sub_style=sub_style,
            callback=status_callback
        )

        if status_callback: status_callback("✅ Xử lý hoàn tất!")
        return final_output
    
    except Exception as e:
        if status_callback: status_callback(f"❌ Lỗi: {str(e)}")
        raise e
    finally:
        for f in [video_file, audio_file, "temp_subtitles.srt"]:
            if os.path.exists(f) and f != video_file:
                try: os.remove(f)
                except: pass
        if os.path.exists(video_file):
            try: os.remove(video_file)
            except: pass
