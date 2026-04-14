import streamlit as st
import asyncio
import edge_tts
import os
import pandas as pd
import zipfile
from io import BytesIO

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
st.set_page_config(page_title="Toktagorn Audio Batch", page_icon="🎙️")
st.title("🎙️ ตกตะกอน: Flexible Audio Batch")

# เมนูเลือกเสียง
voice_options = {
    "ผู้หญิง - Premwadee": "th-TH-PremwadeeNeural",
    "ผู้ชาย - Niwat": "th-TH-NiwatNeural",
}
selected_voice = st.selectbox("เลือกเสียงที่ต้องการ:", list(voice_options.keys()))

# --- 4. ส่วน Browse ไฟล์ ---
uploaded_file = st.file_uploader("📂 เลือกไฟล์ Excel หรือ CSV:", type=['xlsx', 'csv'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.write("✅ โหลดไฟล์สำเร็จ! ตรวจสอบ Column ด้านล่าง:")
        
        # --- จุดเด่นใหม่: ให้พี่เลือก Column เองได้เลยถ้าชื่อไม่ตรง ---
        all_columns = df.columns.tolist()
        
        col_name, col_text = st.columns(2)
        with col_name:
            # พยายามเดาชื่อ Column สำหรับ Sound Name
            default_name_idx = all_columns.index('Sound Name') if 'Sound Name' in all_columns else 0
            name_col = st.selectbox("เลือก Column สำหรับ 'ชื่อไฟล์':", all_columns, index=default_name_idx)
            
        with col_text:
            # พยายามเดาชื่อ Column สำหรับ Text
            default_text_idx = all_columns.index('text') if 'text' in all_columns else 0
            text_col = st.selectbox("เลือก Column สำหรับ 'ข้อความที่พูด':", all_columns, index=default_text_idx)

        if st.button("🚀 เริ่มสร้างเสียง AI ทั้งหมด"):
            generated_files = []
            progress_bar = st.progress(0)
            
            for i, row in df.iterrows():
                f_name = str(row[name_col]).strip()
                f_text = str(row[text_col]).strip()
                
                if f_text and f_text != 'nan':
                    output_filename = f"{f_name}.mp3"
                    asyncio.run(generate_voice(f_text, voice_options[selected_voice], output_filename))
                    generated_files.append(output_filename)
                
                progress_bar.progress((i + 1) / len(df))

            if generated_files:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for f in generated_files:
                        if os.path.exists(f):
                            zf.write(f)
                            os.remove(f)
                
                st.success(f"สร้างสำเร็จ {len(generated_files)} ไฟล์!")
                st.download_button("📥 ดาวน์โหลด ZIP", zip_buffer.getvalue(), "voices.zip")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
