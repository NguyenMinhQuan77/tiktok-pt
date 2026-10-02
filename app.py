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
with col1:
    use_voiceover = st.checkbox("🎙️ Lồng tiếng Việt (AI Voice)", value=True, help="Tắt tiếng gốc và lồng tiếng Việt vào video")
with col2:
    use_subtitles = st.checkbox("📝 Dịch & hiện phụ đề (Sub)", value=False, help="Tính năng hiện chữ đang được tối ưu cho Windows (Yêu cầu ImageMagick).")

# --- PHẦN 3: TÙY CHỌN AFFILIATE ---
st.header("3. Tùy chọn gắn link Sản phẩm")
use_affiliate = st.checkbox("🛒 Gắn link sản phẩm Affiliate vào video", value=False)

selected_product_name = None
if use_affiliate:
    selected_product_name = st.selectbox(
        "Sản phẩm sẽ ghim vào video (lấy từ Showcase của bạn):",
        [p["name"] for p in MOCK_PRODUCTS]
    )
else:
    st.info("💡 Bạn đã chọn chỉ Reup video (không gắn sản phẩm).")

# --- PHẦN 4: THỰC THI ---
st.markdown("---")
if st.button("🚀 BẮT ĐẦU XỬ LÝ & TỰ ĐỘNG ĐĂNG VIDEO", use_container_width=True, type="primary"):
    if not video_url:
        st.error("⚠️ Vui lòng nhập link video!")
    else:
        st.info("Bắt đầu quy trình tự động hóa...")
        
        # Vùng chứa log trạng thái
        status_text = st.empty()
        
        try:
            # Chạy pipeline xử lý video bằng AI
            final_video = asyncio.run(process_video(
                url=video_url,
                use_voiceover=use_voiceover,
                use_subtitles=use_subtitles,
                status_callback=status_text.info
            ))
            
            if final_video and os.path.exists(final_video):
                st.success("✅ Đã xử lý xong video bằng AI!")
                st.video(final_video)
                
                # --- GIẢ LẬP BƯỚC ĐĂNG TẢI QUA API TIKTOK ---
                st.header("4. Đăng tải lên Mạng Xã Hội")
                
                # Đọc thông tin tài khoản từ file account.txt
                account_info = "Chưa cấu hình tài khoản"
                if os.path.exists("account.txt"):
                    with open("account.txt", "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.strip() and not line.startswith("#"):
                                parts = line.strip().split("|")
                                if len(parts) >= 1:
                                    account_info = parts[0] # Chỉ lấy username hiển thị
                                break
                
                upload_status = st.empty()
                upload_status.warning(f"🔄 Đang kết nối kênh TikTok (Tài khoản: **{account_info}**)...")
                time.sleep(2)
                
                if use_affiliate and selected_product_name:
                    upload_status.warning(f"🛒 Đang gắn link sản phẩm: **{selected_product_name}** vào giỏ hàng video...")
                    time.sleep(2)
                    upload_status.success(f"🎉 ĐĂNG THÀNH CÔNG! Video đã lên xu hướng kèm link sản phẩm Affiliate.")
                else:
                    upload_status.success(f"🎉 ĐĂNG THÀNH CÔNG! Video Reup thuần (không gắn Affiliate) đã được đăng tải.")
                
                st.balloons()
            else:
                st.error("❌ Xử lý thất bại, không tìm thấy file đầu ra.")
        except Exception as e:
            st.error(f"❌ Lỗi hệ thống: {e}")
            st.info("Vui lòng kiểm tra lại link video hoặc đảm bảo bạn đã cài FFmpeg.")

