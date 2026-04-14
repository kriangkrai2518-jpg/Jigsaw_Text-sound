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
st.set_page_config(page_title="Toktagorn Auto-Audio", page_icon="🎙️", layout="wide")
st.title("🎙️ ตกตะกอน: Auto-Batch Generator & Editor")

# เมนูเลือกเสียง
voice_options = {
    "ผู้หญิง - Premwadee": "th-TH-PremwadeeNeural",
    "ผู้ชาย - Niwat": "th-TH-NiwatNeural",
}
selected_voice = st.selectbox("เลือกเสียงหลัก:", list(voice_options.keys()))

# --- 4. ส่วน Browse ไฟล์ ---
uploaded_file = st.file_uploader("📂 เลือกไฟล์ Excel หรือ CSV:", type=['xlsx', 'csv'])

if uploaded_file is not None:
    # โหลดข้อมูลใส่ Session State เพื่อไม่ให้หายเวลา Refresh
    if 'df' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.session_state.last_file = uploaded_file.name
        st.session_state.auto_run_done = False # รีเซ็ตสถานะเพื่อให้รันใหม่เมื่อเปลี่ยนไฟล์

    df = st.session_state.df
    all_columns = df.columns.tolist()
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        name_col = st.selectbox("Column ชื่อไฟล์:", all_columns, index=all_columns.index('Sound Name') if 'Sound Name' in all_columns else 0)
    with col_sel2:
        text_col = st.selectbox("Column ข้อความ:", all_columns, index=all_columns.index('text') if 'text' in all_columns else 0)

    # --- 5. ระบบ Auto-Generate (รันอัตโนมัติครั้งแรกที่โหลดไฟล์) ---
    if not st.session_state.get('auto_run_done', False):
        progress_text = st.empty()
        auto_progress = st.progress(0)
        for i, row in df.iterrows():
            f_name = str(row[name_col]).strip()
            f_text = str(row[text_col]).strip()
            if f_text and f_text != 'nan':
                output_file = f"{f_name}.mp3"
                asyncio.run(generate_voice(f_text, voice_options[selected_voice], output_file))
                st.session_state[f"path_{i}"] = output_file
            auto_progress.progress((i + 1) / len(df))
            progress_text.text(f"กำลังเตรียมเสียงอัตโนมัติ: {f_name}")
        st.session_state.auto_run_done = True
        progress_text.empty()
        auto_progress.empty()
        st.success("✅ เตรียมเสียงเบื้องต้นเสร็จแล้ว! พี่เกรียงตรวจสอบและแก้ไขด้านล่างได้เลย")

    st.divider()

    # --- 6. รายการตรวจสอบและแก้ไข ---
    st.subheader("🔍 ตรวจสอบและแก้ไขรายรายการ (ถ้าไม่พอใจกดสร้างใหม่ได้)")
    
    for i, row in df.iterrows():
        f_name = str(row[name_col]).strip()
        f_text = str(row[text_col]).strip()
        
        with st.expander(f"📁 {f_name}.mp3", expanded=False):
            c1, c2, c3 = st.columns([3, 1, 2])
            with c1:
                input_text = st.text_area("ข้อความ:", value=f_text, key=f"input_{i}", height=70)
            with c2:
                st.write("")
                if st.button("🔊 สร้างใหม่", key=f"re_gen_{i}"):
                    output_file = f"{f_name}.mp3"
                    asyncio.run(generate_voice(input_text, voice_options[selected_voice], output_file))
                    st.session_state[f"path_{i}"] = output_file
                    st.toast(f"อัปเดตเสียง {f_name} แล้ว")
            with c3:
                if f"path_{i}" in st.session_state:
                    st.audio(st.session_state[f"path_{i}"])

    # --- 7. ปุ่มรวม ZIP ---
    st.divider()
    if st.button("📦 แพ็กไฟล์ทั้งหมดเป็น ZIP"):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            count = 0
            for i in range(len(df)):
                path_key = f"path_{i}"
                if path_key in st.session_state:
                    file_path = st.session_state[path_key]
                    if os.path.exists(file_path):
                        zf.write(file_path)
                        count += 1
            
        if count > 0:
            st.success(f"รวมไฟล์เสร็จแล้ว {count} ไฟล์")
            st.download_button("📥 ดาวน์โหลด ZIP", zip_buffer.getvalue(), "toktagorn_voices.zip")
        else:
            st.warning("ยังไม่มีไฟล์เสียงที่ถูกสร้างครับ")
