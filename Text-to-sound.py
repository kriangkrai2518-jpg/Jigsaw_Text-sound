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
st.set_page_config(page_title="Toktagorn Audio Editor", page_icon="🎙️", layout="wide")
st.title("🎙️ ตกตะกอน: Audio Verify & Edit")
st.write("ตรวจสอบเสียงและแก้ไขก่อนดาวน์โหลดไฟล์ ZIP")

# เมนูเลือกเสียง
voice_options = {
    "ผู้หญิง - Premwadee": "th-TH-PremwadeeNeural",
    "ผู้ชาย - Niwat": "th-TH-NiwatNeural",
}
selected_voice = st.selectbox("เลือกเสียงหลัก:", list(voice_options.keys()))

# --- 4. ส่วน Browse ไฟล์ ---
uploaded_file = st.file_uploader("📂 เลือกไฟล์ Excel หรือ CSV:", type=['xlsx', 'csv'])

if uploaded_file is not None:
    if 'data_df' not in st.session_state:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.data_df = pd.read_csv(uploaded_file)
        else:
            st.session_state.data_df = pd.read_excel(uploaded_file)
    
    df = st.session_state.data_df
    all_columns = df.columns.tolist()
    
    c1, c2 = st.columns(2)
    with c1:
        name_col = st.selectbox("Column ชื่อไฟล์:", all_columns, index=all_columns.index('Sound Name') if 'Sound Name' in all_columns else 0)
    with c2:
        text_col = st.selectbox("Column ข้อความ:", all_columns, index=all_columns.index('text') if 'text' in all_columns else 0)

    st.divider()

    # --- 5. ส่วนตรวจสอบและเจนเสียง (ทีละไฟล์) ---
    st.subheader("🔍 ตรวจสอบและแก้ไขเสียงทีละรายการ")
    
    generated_audio_paths = {} # เก็บ path ไฟล์ที่สร้างสำเร็จแล้ว

    for i, row in df.iterrows():
        f_name = str(row[name_col]).strip()
        f_text = str(row[text_col]).strip()
        
        with st.expander(f"📁 ไฟล์: {f_name}.mp3", expanded=True):
            col_text, col_action, col_audio = st.columns([3, 1, 2])
            
            with col_text:
                new_text = st.text_area(f"ข้อความสำหรับ {f_name}:", value=f_text, key=f"text_{i}", height=70)
            
            with col_action:
                st.write("") # เว้นระยะ
                if st.button(f"🔊 สร้างเสียง", key=f"btn_{i}"):
                    output_file = f"{f_name}.mp3"
                    asyncio.run(generate_voice(new_text, voice_options[selected_voice], output_file))
                    st.session_state[f"path_{i}"] = output_file
                    st.toast(f"สร้างเสียง {f_name} สำเร็จ!")

            with col_audio:
                if f"path_{i}" in st.session_state:
                    st.audio(st.session_state[f"path_{i}"])
                    generated_audio_paths[f_name] = st.session_state[f"path_{i}"]

    st.divider()

    # --- 6. ส่วนสุดท้าย: รวมไฟล์ ZIP ---
    st.subheader("📦 รวมไฟล์ที่ตรวจสอบเสร็จแล้ว")
    
    # นับจำนวนไฟล์ที่สร้างเสร็จแล้ว
    ready_count = len([k for k in st.session_state.keys() if k.startswith("path_")])
    st.write(f"สร้างเสียงเสร็จแล้ว {ready_count} จาก {len(df)} รายการ")

    if st.button("🎁 กดเพื่อสร้างไฟล์ ZIP สำหรับดาวน์โหลด"):
        if ready_count > 0:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                # วนลูปเช็คไฟล์ที่ถูกสร้างไว้ใน session
                for i in range(len(df)):
                    path_key = f"path_{i}"
                    if path_key in st.session_state:
                        actual_file = st.session_state[path_key]
                        if os.path.exists(actual_file):
                            zf.write(actual_file)
            
            st.success("✅ ไฟล์ ZIP พร้อมแล้ว!")
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ ZIP ทั้งหมด",
                data=zip_buffer.getvalue(),
                file_name="toktagorn_final_voices.zip",
                mime="application/zip"
            )
        else:
            st.warning("กรุณากดปุ่ม 'สร้างเสียง' ในแต่ละรายการที่ต้องการก่อนครับ")

st.divider()
st.caption("ระบบตรวจสอบและแก้ไขเสียง โดย Jigsaw Master")
