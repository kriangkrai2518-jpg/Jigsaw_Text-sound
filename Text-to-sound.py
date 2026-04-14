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

# เลือกเสียง
voice_options = {
    "ผู้หญิง - Premwadee": "th-TH-PremwadeeNeural",
    "ผู้ชาย - Niwat": "th-TH-NiwatNeural",
}
selected_voice = st.selectbox("เลือกเสียงหลัก:", list(voice_options.keys()))

# --- 4. ส่วน Browse ไฟล์ ---
uploaded_file = st.file_uploader("📂 เลือกไฟล์ Excel หรือ CSV:", type=['xlsx', 'csv'])

if uploaded_file is not None:
    # โหลดไฟล์เข้า Session
    if 'df' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.session_state.last_file = uploaded_file.name
        st.session_state.auto_run_done = False 
        # เคลียร์เสียงเก่า
        for key in list(st.session_state.keys()):
            if key.startswith("path_"): del st.session_state[key]

    df = st.session_state.df
    all_columns = df.columns.tolist()
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        # พยายามเดาชื่อไฟล์
        idx_name = all_columns.index('Sound Name') if 'Sound Name' in all_columns else 0
        name_col = st.selectbox("Column ชื่อไฟล์:", all_columns, index=idx_name)
    with col_sel2:
        # พยายามเดา Column ข้อความ (ถ้ามีคำว่า text หรือข้อความยาวๆ)
        idx_text = all_columns.index('text') if 'text' in all_columns else (1 if len(all_columns) > 1 else 0)
        text_col = st.selectbox("Column ข้อความที่พูด:", all_columns, index=idx_text)

    # --- 5. ระบบรันอัตโนมัติ (ทันทีที่โหลด) ---
    if not st.session_state.get('auto_run_done', False):
        with st.status("🚀 กำลังตกตะกอนเสียงให้อัตโนมัติ...", expanded=True) as status:
            for i, row in df.iterrows():
                f_name = str(row[name_col]).strip()
                f_text = str(row[text_col]).strip()
                if f_text and f_text != 'nan':
                    output_file = f"{f_name}.mp3"
                    asyncio.run(generate_voice(f_text, voice_options[selected_voice], output_file))
                    st.session_state[f"path_{i}"] = output_file
            st.session_state.auto_run_done = True
            status.update(label="✅ เตรียมเสียงเสร็จเรียบร้อย!", state="complete", expanded=False)

    st.divider()

    # --- 6. รายการตรวจสอบและแก้ไข ---
    st.subheader("🔍 รายการเสียง (แก้ไขและเจนใหม่ได้รายอัน)")
    
    for i, row in df.iterrows():
        f_name = str(row[name_col]).strip()
        f_text = str(row[text_col]).strip()
        
        with st.expander(f"📁 {f_name}.mp3", expanded=True):
            c1, c2, c3 = st.columns([3, 1, 2])
            with c1:
                # ช่องใส่ข้อความที่ดึงมาจาก Excel อัตโนมัติ
                input_text = st.text_area(f"ข้อความ ({f_name}):", value=f_text, key=f"input_{i}", height=80)
            with c2:
                st.write("")
                if st.button("🔊 เจนซ้ำ", key=f"re_gen_{i}"):
                    output_file = f"{f_name}.mp3"
                    asyncio.run(generate_voice(input_text, voice_options[selected_voice], output_file))
                    st.session_state[f"path_{i}"] = output_file
                    st.toast(f"อัปเดตเสียง {f_name} แล้ว!")
            with c3:
                if f"path_{i}" in st.session_state:
                    st.audio(st.session_state[f"path_{i}"])

    # --- 7. ปุ่ม ZIP ---
    st.divider()
    if st.button("📦 แพ็กไฟล์ที่ตรวจแล้วเป็น ZIP"):
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
            st.success(f"รวมสำเร็จ {count} ไฟล์")
            st.download_button("📥 ดาวน์โหลด ZIP", zip_buffer.getvalue(), "toktagorn_final.zip")
