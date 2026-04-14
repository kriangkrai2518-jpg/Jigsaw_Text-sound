import streamlit as st
import asyncio
import edge_tts
import os
import pandas as pd
from io import BytesIO
import zipfile

# --- 1. ระบบจัดการคำอ่าน ---
def clean_text_for_ai(text):
    pronunciation_map = {
        "Python": "ไพ-ธอน", "Jigsaw": "จิก-ซอ",
        "Branding": "แบรน-ดิ้ง", "ตกตะกอน": "ตก-ตะ-กอน", "AI": "เอ-ไอ"
    }
    for word, pronunciation in pronunciation_map.items():
        text = text.replace(str(word), str(pronunciation))
    return text

# --- 2. ฟังก์ชันสร้างเสียง ---
async def generate_voice(text, voice, output_file):
    processed_text = clean_text_for_ai(text)
    communicate = edge_tts.Communicate(processed_text, voice)
    await communicate.save(output_file)

# --- 3. หน้าตาเว็บ ---
st.title("🎙️ Toktagorn: Batch Voice Generator")
st.write("สร้างไฟล์เสียงหลายไฟล์พร้อมกัน สำหรับระบบ Jigsaw Master")

# เมนูเลือกเสียง
voice_options = {
    "ผู้หญิง - Premwadee": "th-TH-PremwadeeNeural",
    "ผู้ชาย - Niwat": "th-TH-NiwatNeural",
    "ผู้หญิงใส - Achara": "th-TH-AcharaNeural",
}
selected_voice = st.selectbox("เลือกเสียงหลัก:", list(voice_options.keys()))

# --- 4. ส่วนนำเข้าข้อมูล (Bulk Input) ---
st.subheader("1. ใส่ข้อมูลที่ต้องการสร้าง")
# ให้พี่เกรียงก๊อปปี้จาก Google Sheet มาวางในนี้ได้เลย
input_data = st.text_area("วางข้อมูล (ลำดับ, ข้อความ) เช่น:\nS1, สวัสดีครับ\nS2, ยินดีต้อนรับ", height=200)

if st.button("🚀 เริ่มสร้างไฟล์ทั้งหมด"):
    if input_data:
        lines = input_data.strip().split('\n')
        generated_files = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, line in enumerate(lines):
            try:
                # แยกข้อมูลด้วย comma (รูปแบบ: ชื่อไฟล์, ข้อความ)
                parts = line.split(',', 1)
                if len(parts) < 2: continue
                
                f_name = parts[0].strip()
                f_text = parts[1].strip()
                output_filename = f"{f_name}.mp3"
                
                # สั่งสร้างเสียง
                asyncio.run(generate_voice(f_text, voice_options[selected_voice], output_filename))
                generated_files.append(output_filename)
                
                # อัปเดตสถานะ
                progress = (i + 1) / len(lines)
                progress_bar.progress(progress)
                status_text.text(f"กำลังสร้าง: {output_filename}")
                
            except Exception as e:
                st.error(f"Error at {line}: {e}")

        # --- 5. ระบบบีบอัดไฟล์ (Zip) เพื่อให้โหลดทีเดียวได้ ---
        if generated_files:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for f in generated_files:
                    zf.write(f)
                    os.remove(f) # ลบไฟล์ออกจากเซิร์ฟเวอร์หลังใส่ Zip
            
            st.success(f"สร้างเสร็จสมบูรณ์ทั้งหมด {len(generated_files)} ไฟล์!")
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ทั้งหมด (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="toktagorn_voices.zip",
                mime="application/zip"
            )
    else:
        st.warning("กรุณาใส่ข้อมูลก่อนครับ")
