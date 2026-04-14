from gtts import gTTS
import os

def generate_voice_from_sheet(scene_text, output_filename):
    # 1. ปรับปรุงคำอ่านก่อน
    processed_text = clean_text_for_ai(scene_text)
    
    # 2. สร้างเสียง (รองรับเครื่องหมาย , . และการเว้นวรรค)
    tts = gTTS(text=processed_text, lang='th')
    
    # 3. บันทึกไฟล์
    tts.save(f"{output_filename}.mp3")
    print(f"สร้างไฟล์ {output_filename}.mp3 สำเร็จ!")

# สมมติข้อมูลจากแถวแรกใน Sheet ของพี่
text_from_sheet = "สวัสดีครับ, ผมเกรียง จากเพจ ตกตะกอน. วันนี้จะมาสอน Python ครับ"
filename_from_sheet = "P1S1"

generate_voice_from_sheet(text_from_sheet, filename_from_sheet)
