import streamlit as st
import asyncio
import edge_tts
import os

# --- 1. ตั้งค่าคำอ่านเฉพาะทาง ---
def clean_text_for_ai(text):
    pronunciation_map = {
        "Python": "ไพ-ธอน",
        "Jigsaw": "จิก-ซอ",
        "Branding": "แบรน-ดิ้ง",
        "ตกตะกอน": "ตก-ตะ-กอน",
        "AI": "เอ-ไอ"
    }
    for word, pronunciation in pronunciation_map.items():
        text = text.replace(word, pronunciation)
    return text

# --- 2. ฟังก์ชันสร้างเสียงด้วย Edge-TTS ---
async def generate_voice(text, voice, output_file):
    processed_text = clean_text_for_ai(text)
    communicate = edge_tts.Communicate(processed_text, voice)
    await communicate.save(output_file)

# --- 3. หน้าตาเว็บ Streamlit ---
st.set_page_config(page_title="Toktagorn Multi-Voice AI", page_icon="🎙️")
st.title("🎙️ ตกตะกอน: Multi-Voice System")
st.write("เลือกเสียง AI ชาย-หญิง ได้หลากหลายรูปแบบ")

# --- 4. เมนูเลือกเสียง (ชาย/หญิง) ---
voice_options = {
    "ผู้หญิง - เสียงนุ่มนวล (Premwadee)": "th-TH-PremwadeeNeural",
    "ผู้ชาย - เสียงทางการ (Niwat)": "th-TH-NiwatNeural",
    "ผู้หญิง - เสียงใส (Achara)": "th-TH-AcharaNeural",
}

selected_voice_label = st.selectbox("เลือกเสียงที่ต้องการ:", list(voice_options.keys()))
selected_voice = voice_options[selected_voice_label]

# --- 5. ส่วนรับข้อความ ---
text_input = st.text_area("ใส่ข้อความที่นี่:", placeholder="สวัสดีครับพี่เกรียง...")
file_name = st.text_input("ชื่อไฟล์ (ไม่ต้องใส่ .mp3):", value="output_audio")

if st.button("🚀 เริ่มสร้างเสียง AI"):
    if text_input:
        output_file = f"{file_name}.mp3"
        try:
            with st.spinner('กำลังสร้างเสียง...'):
                # รันฟังก์ชันสร้างเสียงแบบ Async
                asyncio.run(generate_voice(text_input, selected_voice, output_file))
                
                # แสดงผล
                st.success(f"สร้างเสียง '{selected_voice_label}' สำเร็จ!")
                
                with open(output_file, "rb") as f:
                    audio_bytes = f.read()
                    st.audio(audio_bytes, format='audio/mp3')
                
                st.download_button(
                    label="📥 ดาวน์โหลดไฟล์เสียง",
                    data=audio_bytes,
                    file_name=output_file,
                    mime="audio/mp3"
                )
                
                os.remove(output_file)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        st.warning("กรุณาใส่ข้อความก่อนครับ")
