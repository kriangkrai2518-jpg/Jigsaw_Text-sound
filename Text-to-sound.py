import streamlit as st
from gtts import gTTS
import os

# --- 1. ส่วนตั้งค่าการออกเสียง (Dictionary) ---
# พี่เกรียงสามารถเพิ่มคำเฉพาะของเพจ "ตกตะกอน" ได้ที่นี่เรื่อยๆ ครับ
def clean_text_for_ai(text):
    pronunciation_map = {
        "Python": "ไพ-ธอน",
        "Jigsaw": "จิก-ซอ",
        "Branding": "แบรน-ดิ้ง",
        "ตกตะกอน": "ตก-ตะ-กอน",
        "AI": "เอ-ไอ",
        "Youtube": "ยู-ทูป",
        "Shorts": "ช็อร์ต"
    }
    for word, pronunciation in pronunciation_map.items():
        text = text.replace(word, pronunciation)
    return text

# --- 2. ส่วนการตั้งค่าหน้าเว็บ Streamlit ---
st.set_page_config(page_title="Toktagorn Text-to-Sound", page_icon="🎙️")

st.title("🎙️ ตกตะกอน: AI Text-to-Sound")
st.subheader("ระบบสร้างเสียงสำหรับ Jigsaw Master")
st.write("จัดการคำทับศัพท์และจูนจังหวะการพูดด้วย Comma (,) และ Full Stop (.)")

# --- 3. ส่วนรับข้อมูลจากผู้ใช้ ---
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        text_input = st.text_area("ใส่ข้อความที่ต้องการ (ใช้ , หรือ . เพื่อเว้นจังหวะ):", 
                                  placeholder="ตัวอย่าง: สวัสดีครับ, ผมเกรียง จากเพจ ตก-ตะ-กอน.")
    with col2:
        file_name = st.text_input("ชื่อไฟล์ไฟล์:", value="output_audio")

# --- 4. ส่วนประมวลผล ---
if st.button("🚀 เริ่มสร้างเสียง AI"):
    if text_input:
        try:
            with st.spinner('ระบบกำลังตกตะกอนเสียง...'):
                # จัดการคำอ่าน
                processed_text = clean_text_for_ai(text_input)
                
                # สร้างเสียงด้วย gTTS
                tts = gTTS(text=processed_text, lang='th')
                
                # บันทึกไฟล์ชั่วคราว
                temp_file = f"{file_name}.mp3"
                tts.save(temp_file)
                
                # แสดงผลสำเร็จ
                st.success(f"สร้างไฟล์ {temp_file} สำเร็จแล้ว!")
                
                # แสดงเครื่องเล่นเสียงบนหน้าเว็บ
                with open(temp_file, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format='audio/mp3')
                
                # ปุ่ม Download ไฟล์
                st.download_button(
                    label="📥 ดาวน์โหลดไฟล์เสียง",
                    data=audio_bytes,
                    file_name=temp_file,
                    mime="audio/mp3"
                )
                
                # ลบไฟล์ชั่วคราวออกจากระบบ Cloud (เพื่อความสะอาด)
                os.remove(temp_file)
                
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
    else:
        st.warning("กรุณาใส่ข้อความก่อนกดปุ่มครับพี่เกรียง")

# --- 5. ส่วนคำแนะนำเพิ่มเติม ---
st.divider()
st.info("""
**💡 เทคนิคการจูนเสียงให้ประณีต:**
- ใช้ **Comma ( , )** เพื่อหยุดพักสั้นๆ
- ใช้ **Full Stop ( . )** เพื่อจบประโยคและเน้นเสียงต่ำ
- ใช้ **การเว้นวรรค** เพื่อเว้นจังหวะระหว่างคำ
- คำทับศัพท์ภาษาอังกฤษ ระบบจะเปลี่ยนเป็นคำอ่านไทยให้อัตโนมัติ (ตามที่ตั้งค่าไว้)
""")
