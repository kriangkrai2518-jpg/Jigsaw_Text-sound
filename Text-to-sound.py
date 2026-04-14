from gtts import gTTS
import os

# --- 1. ต้องมีฟังก์ชันนี้วางไว้ด้านบนก่อน ---
def clean_text_for_ai(text):
    pronunciation_map = {
        "Python": "ไพ-ธอน",
        "Jigsaw": "จิก-ซอ",
        "Branding": "แบรน-ดิ้ง",
        "ตกตะกอน": "ตก-ตะ-กอน"
    }
    for word, pronunciation in pronunciation_map.items():
        text = text.replace(word, pronunciation)
    return text

# --- 2. ฟังก์ชันหลักที่เรียกใช้ตัวข้างบน ---
def generate_voice_from_sheet(scene_text, output_filename):
    processed_text = clean_text_for_ai(scene_text) # <--- จุดที่เกิด Error เพราะหาบรรทัดบนไม่เจอ
    tts = gTTS(text=processed_text, lang='th')
    tts.save(f"{output_filename}.mp3")

# --- 3. ส่วนที่สั่งรัน (Execution) อยู่ล่างสุด ---
text_from_sheet = "สวัสดีครับ, ผมเกรียง"
filename_from_sheet = "P1S1"
generate_voice_from_sheet(text_from_sheet, filename_from_sheet)
