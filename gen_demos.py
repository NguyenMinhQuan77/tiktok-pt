import os, subprocess

srt_content = '''1
00:00:00,000 --> 00:00:01,000
Đây là chữ mẫu (Vietsub)
'''
with open('demo.srt', 'w', encoding='utf-8') as f:
    f.write(srt_content)

styles = {
    'demos/style1.jpg': "Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,Outline=1",
    'demos/style2.jpg': "Fontname=Arial,Fontsize=22,PrimaryColour=&H0000FFFF,Outline=2",
    'demos/style3.jpg': "Fontname=Arial,Fontsize=26,PrimaryColour=&H00FFFFFF,Outline=3",
    'demos/style4.jpg': "Fontname=Arial,Fontsize=22,PrimaryColour=&H0000FF00,Outline=2"
}

os.makedirs('demos', exist_ok=True)
for img, force_style in styles.items():
    cmd = [
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=gray:s=720x1280:d=1',
        '-vf', f"subtitles=demo.srt:force_style='{force_style}'",
        '-frames:v', '1', img
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f'Generated {img}')
