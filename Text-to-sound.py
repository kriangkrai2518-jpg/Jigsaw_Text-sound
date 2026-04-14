import streamlit as st
import asyncio
import edge_tts
import os
import gspread
from google.oauth2.service_account import Credentials
import zipfile
from io import BytesIO

# --- 1. ตั้งค่าการเชื่อมต่อ Google Sheets ---
def connect_to_sheet(sheet_url, sheet_name):
    # ดึงข้อมูลจาก Streamlit Secrets (เพื่อความปลอดภัย ไม่ควรวาง JSON ในโค้ด)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"] # พี่ต้องเอาข้อมูล JSON ไปใส่ใน Streamlit Secrets
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    return sheet

# --- 2. ฟังก์ชันสร้างเสียง ---
async def generate_voice(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

# --- 3. หน้าตาเว็บ ---
st.title("🎙️ Toktagorn: Google Sheet to Voice")
st.write("ดึงข้อมูลจาก Sheet มาสร้างเสียงอัตโนมัติ")

# รับค่าจาก User
sheet_url = st.text_input("วางลิงก์ Google Sheet ของพี่ที่นี่:")
sheet_name = st.text_input("ชื่อ Worksheet (เช่น Sheet1):", value="Sheet1")

voice_options = {
    "ผู้หญิง - Premwadee": "th-TH-PremwadeeNeural",
    "ผู้ชาย - Niwat": "th-TH-NiwatNeural"
}
selected_voice = st.selectbox("เลือกเสียงหลัก:", list(voice_options.keys()))

if st.button("🚀 ดึงข้อมูลและเริ่มสร้างเสียง"):
    if sheet_url:
        try:
            sheet = connect_to_sheet(sheet_url, sheet_name)
            data = sheet.get_all_records() # ดึงข้อมูลทั้งหมดในรูป Dictionary
            
            generated_files = []
            progress_bar = st.progress(0)
            
            for i, row in enumerate(data):
                # ตรวจสอบชื่อ Column ให้ตรงกับในรูป Image 3 (Sound Name และ text)
                f_name = str(row.get('Sound Name', f'audio_{i}'))
                f_text = str(row.get('text', ''))
                
                if f_text:
                    output_filename = f"{f_name}.mp3"
                    asyncio.run(generate_voice(f_text, voice_options[selected_voice], output_filename))
                    generated_files.append(output_filename)
                
                progress_bar.progress((i + 1) / len(data))

            # รวมไฟล์เป็น ZIP
            if generated_files:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for f in generated_files:
                        zf.write(f)
                        os.remove(f)
                
                st.success(f"สร้างสำเร็จ {len(generated_files)} ไฟล์!")
                st.download_button("📥 ดาวน์โหลด ZIP", zip_buffer.getvalue(), "voices.zip")
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        st.warning("กรุณาใส่ลิงก์ Google Sheet ก่อนครับพี่เกรียง")
