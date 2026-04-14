import streamlit as st
import asyncio
import edge_tts
import os
import pandas as pd
import zipfile
from io import BytesIO

# --- 1. ระบบจัดการคำอ่าน (Dictionary) ---
def clean_text_for_ai(text):
    # ปรับจูนคำอ่านให้ประณีตตามสไตล์เพจตกตะกอน
    pronunciation_map = {
        "Python": "ไพ-ธอน", 
        "Jigsaw": "จิก-ซอ",
        "Branding": "แบรน-ดิ้ง", 
        "ตกตะกอน": "ตก-ตะ-กอน", 
        "AI": "เอ-ไอ"
    }
    for word, pronunciation in pronunciation_map.items():
        text = text.replace(str(word), str(pronunciation))
    return text

# --- 2. ฟังก์ชันสร้างเสียงด้วย Edge-TTS (คุณภาพสูง) ---
async def generate_voice(text, voice, output_file):
    processed_text = clean_text_for_ai(text)
    communicate = edge_tts.Communicate(processed_text, voice)
    await communicate.save(output_file)

# --- 3. ตั้งค่าหน้าตาเว็บ Streamlit ---
st.set_page_config(page_title="Toktagorn Audio Batch", page_icon="🎙️")
st.title("🎙️ ตกตะกอน: Audio Batch Uploader")
st.write("เลือกไฟล์ Excel หรือ CSV จากเครื่องเพื่อสร้างเสียงพร้อมกันหลายไฟล์")

# เมนูเลือกเสียง (ชาย/หญิง)
voice_options = {
    "ผู้หญิง - นุ่มนวล (Premwadee)": "th-TH-PremwadeeNeural",
    "ผู้ชาย - ทางการ (Niwat)": "th-TH-NiwatNeural",
    "ผู้หญิง - เสียงใส (Achara)": "th-TH-AcharaNeural",
}
selected_voice = st.selectbox("เลือกโทนเสียงที่ต้องการ:", list(voice_options.keys()))

# --- 4. ส่วน Browse ไฟล์จาก PC ---
uploaded_file = st.file_uploader("📂 เลือกไฟล์จากเครื่องของพี่ (Excel หรือ CSV):", type=['xlsx', 'csv'])

if uploaded_file is not None:
    try:
        # ตรวจสอบนามสกุลไฟล์และอ่านข้อมูล
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"โหลดไฟล์ '{uploaded_file.name}' สำเร็จ!")
        st.write("---")
        st.write("🔍 ตรวจสอบข้อมูล 5 แถวแรก:")
        st.dataframe(df.head())

        # ปุ่มเริ่มทำงาน
        if st.button("🚀 เริ่มสร้างเสียง AI ทั้งหมด"):
            # ตรวจสอบชื่อ Column (ต้องตรงกับใน Google Sheet ของพี่)
            # จาก Image 3 ของพี่ Column ชื่อ 'Sound Name' และ 'text'
            if 'Sound Name' in df.columns and 'text' in df.columns:
                generated_files = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, row in df.iterrows():
                    f_name = str(row['Sound Name']).strip()
                    f_text = str(row['text']).strip()
                    
                    if f_text and f_text != 'nan':
                        output_filename = f"{f_name}.mp3"
                        status_text.text(f"กำลังตกตะกอนเสียง: {output_filename}")
                        
                        # รันการสร้างเสียง
                        asyncio.run(generate_voice(f_text, voice_options[selected_voice], output_filename))
                        generated_files.append(output_filename)
                    
                    # อัปเดต Progress Bar
                    progress_bar.progress((i + 1) / len(df))

                # --- 5. การรวบรวมไฟล์เป็น ZIP ---
                if generated_files:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for f in generated_files:
                            if os.path.exists(f):
                                zf.write(f)
                                os.remove(f) # ลบไฟล์ออกจากระบบหลังรวมใส่ Zip เพื่อความสะอาด
                    
                    st.success(f"✅ สร้างเสร็จสมบูรณ์ทั้งหมด {len(generated_files)} ไฟล์!")
                    
                    # ปุ่มดาวน์โหลด
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์เสียงทั้งหมด (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="toktagorn_voices_pack.zip",
                        mime="application/zip"
                    )
            else:
                st.error("❌ ไม่พบ Column ชื่อ 'Sound Name' หรือ 'text' ในไฟล์ของพี่ครับ")
                st.info("คำแนะนำ: โปรดเช็คตัวพิมพ์เล็ก-ใหญ่ในไฟล์ Excel ให้ตรงกับในโค้ดนะครับ")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")

# --- ส่วนท้าย ---
st.divider()
st.caption("พัฒนาโดยระบบ Jigsaw Master สำหรับเพจ @Toktagorn")
