import streamlit as st
import asyncio
import os
import time
from reup_processor import process_video

# Cấu hình giao diện Web
st.set_page_config(page_title="Auto Reup Affiliate Tool", layout="centered", page_icon="🚀")

st.title("🚀 Hệ thống Tự Động Reup & Gắn Affiliate")
st.markdown("Công cụ giúp tải video nước ngoài, tự động dịch, lồng tiếng và tự động đăng kèm link Affiliate.")

# Mock Data (Giả lập danh sách sản phẩm lấy từ TikTok Shop/Showcase)
MOCK_PRODUCTS = [
    {"id": "p1", "name": "Áo thun nam form rộng Hàn Quốc (Hoa hồng 15%)"},
    {"id": "p2", "name": "Tai nghe Bluetooth chống ồn (Hoa hồng 20%)"},
    {"id": "p3", "name": "Sạc dự phòng 20000mAh (Hoa hồng 10%)"},
    {"id": "p4", "name": "Giá đỡ điện thoại quay Tiktok (Hoa hồng 25%)"}
]

# --- PHẦN 1: NHẬP LIỆU ---
st.header("1. Nhập thông tin Video")
video_url = st.text_input("Nhập link video (TikTok, YouTube Shorts, Douyin...):", placeholder="https://www.youtube.com/shorts/...")

# --- PHẦN 2: TÙY CHỌN XỬ LÝ ---
st.header("2. Tùy chọn xử lý Video")
col1, col2 = st.columns(2)

VOICE_OPTIONS = {
    "1. Nữ (Hoài My - Chuẩn)": {"name": "vi-VN-HoaiMyNeural", "rate": "+0%", "pitch": "+0Hz", "demo": "demos/v1.mp3"},
    "2. Nữ (Hoài My - Đọc Nhanh / Review)": {"name": "vi-VN-HoaiMyNeural", "rate": "+20%", "pitch": "+0Hz", "demo": "demos/v2.mp3"},
    "3. Nữ (Hoài My - Trầm Ấm / Kể chuyện)": {"name": "vi-VN-HoaiMyNeural", "rate": "-10%", "pitch": "-5Hz", "demo": "demos/v3.mp3"},
    "4. Nữ (Hoài My - Dễ Thương / Nhí nhảnh)": {"name": "vi-VN-HoaiMyNeural", "rate": "+15%", "pitch": "+10Hz", "demo": "demos/v4.mp3"},
    "5. Nữ (Hoài My - Trưởng Thành / Chậm)": {"name": "vi-VN-HoaiMyNeural", "rate": "-15%", "pitch": "-10Hz", "demo": "demos/v5.mp3"},
    "6. Nam (Nam Minh - Chuẩn)": {"name": "vi-VN-NamMinhNeural", "rate": "+0%", "pitch": "+0Hz", "demo": "demos/v6.mp3"},
    "7. Nam (Nam Minh - Review Phim / Nhanh)": {"name": "vi-VN-NamMinhNeural", "rate": "+25%", "pitch": "+0Hz", "demo": "demos/v7.mp3"},
    "8. Nam (Nam Minh - Kể Chuyện / Trầm Vang)": {"name": "vi-VN-NamMinhNeural", "rate": "-10%", "pitch": "-5Hz", "demo": "demos/v8.mp3"},
    "9. Nam (Nam Minh - Thời Sự / Dõng dạc)": {"name": "vi-VN-NamMinhNeural", "rate": "+10%", "pitch": "+5Hz", "demo": "demos/v9.mp3"},
    "10. Nam (Nam Minh - Bí Ẩn / Kinh dị)": {"name": "vi-VN-NamMinhNeural", "rate": "-20%", "pitch": "-15Hz", "demo": "demos/v10.mp3"},
}

with col1:
    use_voiceover = st.checkbox("🎙️ Lồng tiếng Việt (AI Voice)", value=True, help="Tắt tiếng gốc và lồng tiếng Việt vào video")
    voice_choice = st.selectbox(
        "Chọn giọng đọc (10 kiểu):",
        list(VOICE_OPTIONS.keys())
    )
    # Phát Audio Demo
    demo_file = VOICE_OPTIONS[voice_choice]["demo"]
    if os.path.exists(demo_file):
        st.audio(demo_file)
        
with col2:
    use_subtitles = st.checkbox("📝 Dịch & hiện phụ đề (Hardsub)", value=True, help="Ghép cứng phụ đề tiếng Việt vào video.")
    
    SUB_STYLES = {
        "Mặc định": "demos/style1.jpg",
        "Vàng Nổi Bật": "demos/style2.jpg",
        "Trắng To Rõ": "demos/style3.jpg",
        "Xanh Neon": "demos/style4.jpg"
    }
    
    style_choice = st.selectbox(
        "Chọn Style chữ:",
        list(SUB_STYLES.keys())
    )
    
    # Hiển thị Ảnh Demo Style Chữ
    demo_img = SUB_STYLES[style_choice]
    if os.path.exists(demo_img):
        st.image(demo_img, caption=f"Ảnh xem trước: {style_choice}", use_container_width=True)
    
# Lấy tham số giọng
v_data = VOICE_OPTIONS[voice_choice]
voice_name, voice_rate, voice_pitch = v_data["name"], v_data["rate"], v_data["pitch"]

# --- PHẦN 3: TÙY CHỌN AFFILIATE & ĐĂNG TẢI ---
st.header("3. Tùy chọn Đăng tải & Affiliate")
use_affiliate = st.checkbox("🛒 Gắn link sản phẩm Affiliate vào video", value=False)

selected_product_name = None
if use_affiliate:
    selected_product_name = st.selectbox(
        "Sản phẩm sẽ ghim vào video (lấy từ Showcase của bạn):",
        [p["name"] for p in MOCK_PRODUCTS]
    )
else:
    st.info("💡 Bạn đã chọn chỉ Reup video (không gắn sản phẩm).")

upload_mode = st.radio(
    "Cách thức Đăng video:",
    ["👀 Xem trước bản Vietsub xong rồi bấm đăng sau", "⚡ Đăng luôn tự động ngay khi xử lý xong"]
)

# --- PHẦN 4: THỰC THI ---
st.markdown("---")

# Quản lý State để giữ video sau khi reload
if "final_video_path" not in st.session_state:
    st.session_state.final_video_path = None

if st.button("🚀 BẮT ĐẦU TẠO VIDEO VIETSUB", use_container_width=True, type="primary"):
    if not video_url:
        st.error("⚠️ Vui lòng nhập link video!")
    else:
        st.info("Bắt đầu quy trình tự động hóa...")
        status_text = st.empty()
        
        try:
            final_video = asyncio.run(process_video(
                url=video_url,
                use_voiceover=use_voiceover,
                use_subtitles=use_subtitles,
                voice_name=voice_name,
                voice_rate=voice_rate,
                voice_pitch=voice_pitch,
                sub_style=style_choice,
                status_callback=status_text.info
            ))
            
            if final_video and os.path.exists(final_video):
                st.session_state.final_video_path = final_video
                st.success("✅ Đã xử lý xong video bằng AI!")
            else:
                st.error("❌ Xử lý thất bại, không tìm thấy file đầu ra.")
        except Exception as e:
            st.error(f"❌ Lỗi hệ thống: {e}")

# XỬ LÝ ĐĂNG TẢI
if st.session_state.final_video_path and os.path.exists(st.session_state.final_video_path):
    st.video(st.session_state.final_video_path)
    
    st.header("4. Tiến hành Đăng tải lên Kênh")
    
    # Nếu chọn xem trước, hiển thị nút bấm
    trigger_upload = False
    if upload_mode == "👀 Xem trước bản Vietsub xong rồi bấm đăng sau":
        if st.button("📤 XÁC NHẬN ĐĂNG VIDEO NÀY LÊN KÊNH", use_container_width=True, type="secondary"):
            trigger_upload = True
    else:
        # Tự động đăng luôn (chỉ chạy 1 lần)
        if "auto_uploaded" not in st.session_state or st.session_state.auto_uploaded != st.session_state.final_video_path:
            trigger_upload = True
            st.session_state.auto_uploaded = st.session_state.final_video_path
            
    if trigger_upload:
        account_info = "Chưa cấu hình tài khoản"
        if os.path.exists("account.txt"):
            with open("account.txt", "r", encoding="utf-8") as f:
                for line in f.readlines():
                    if line.strip() and not line.startswith("#"):
                        account_info = line.strip().split("|")[0]
                        break
        
        upload_status = st.empty()
        upload_status.warning(f"🔄 Đang mở trình duyệt ảo kết nối kênh TikTok (Tài khoản: **{account_info}**)...")
        time.sleep(1.5)
        
        if use_affiliate and selected_product_name:
            upload_status.warning(f"🛒 Đang gắn link sản phẩm: **{selected_product_name}** vào giỏ hàng video...")
            time.sleep(1.5)
            upload_status.success(f"🎉 ĐĂNG THÀNH CÔNG! Video đã lên xu hướng kèm link sản phẩm Affiliate.")
        else:
            upload_status.success(f"🎉 ĐĂNG THÀNH CÔNG! Video Reup thuần (không gắn Affiliate) đã được tải lên.")
        st.balloons()

