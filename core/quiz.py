# =====================================================
# quiz.py — แบบประเมินระดับความเสี่ยงที่ผู้ลงทุนรับได้
#   QUESTIONS  คำถาม 10 ข้อ ข้อละ 4 ตัวเลือก (ตัวเลือกที่ 1–4 ได้ 1–4 คะแนน)
#   LEVELS     ระดับผู้ลงทุน 5 ระดับ + สัดส่วนการลงทุนที่แนะนำเป็นแนวทาง
#   score()    รวมคะแนน → ระดับ
#   save() / load()  บันทึก/อ่านผลล่าสุดของผู้ใช้ในฐานข้อมูล
# โครงสร้างแบบประเมินอ้างอิงแนวทางแบบประเมินความเหมาะสมในการลงทุนที่ใช้กันทั่วไป
# (คะแนนรวม 10–40 แบ่งเป็น 5 ระดับ)
# อยากแก้คำถาม/คะแนน/สัดส่วน → แก้ในไฟล์นี้ที่เดียว
# =====================================================
import json
from datetime import datetime

from core import auth

# รูปแบบ: {"q": {ลาว, อังกฤษ}, "a": [ตัวเลือก 4 ข้อ เรียงจากเสี่ยงต่ำ → เสี่ยงสูง]}
QUESTIONS = [
    {"q": {"lo": "ປັດຈຸບັນທ່ານອາຍຸເທົ່າໃດ?", "en": "How old are you?"},
     "a": [{"lo": "ຫຼາຍກວ່າ 60 ປີ", "en": "Over 60"},
           {"lo": "45–60 ປີ", "en": "45–60"},
           {"lo": "35–44 ປີ", "en": "35–44"},
           {"lo": "ຕ່ຳກວ່າ 35 ປີ", "en": "Under 35"}]},
    {"q": {"lo": "ລາຍຈ່າຍປະຈຳ ແລະ ໜີ້ສິນ (ຄ່າເຊົ່າ, ຜ່ອນເຮືອນ/ລົດ, ຄ່າລ້ຽງດູ) ກິນສັດສ່ວນເທົ່າໃດຂອງລາຍຮັບ?",
           "en": "How much of your income goes to fixed costs and debt (rent, loans, family support)?"},
     "a": [{"lo": "ຫຼາຍກວ່າ 75% ຂອງລາຍຮັບ", "en": "More than 75% of income"},
           {"lo": "50–75% ຂອງລາຍຮັບ", "en": "50–75% of income"},
           {"lo": "25–50% ຂອງລາຍຮັບ", "en": "25–50% of income"},
           {"lo": "ໜ້ອຍກວ່າ 25% ຂອງລາຍຮັບ", "en": "Less than 25% of income"}]},
    {"q": {"lo": "ສະຖານະການເງິນຂອງທ່ານໃນປັດຈຸບັນເປັນແນວໃດ?", "en": "What is your financial position today?"},
     "a": [{"lo": "ຊັບສິນໜ້ອຍກວ່າໜີ້ສິນ", "en": "I own less than I owe"},
           {"lo": "ຊັບສິນເທົ່າກັບໜີ້ສິນ", "en": "I own about as much as I owe"},
           {"lo": "ຊັບສິນຫຼາຍກວ່າໜີ້ສິນ", "en": "I own more than I owe"},
           {"lo": "ມີເງິນອອມພຽງພໍສຳລັບໃຊ້ຫຼັງກະສຽນແລ້ວ", "en": "I already have enough saved for retirement"}]},
    {"q": {"lo": "ທ່ານເຄີຍລົງທຶນ ຫຼື ມີຄວາມຮູ້ໃນຊັບສິນປະເພດໃດ (ເລືອກລະດັບສູງສຸດ)?",
           "en": "Which investments have you used or do you understand (pick the riskiest)?"},
     "a": [{"lo": "ເງິນຝາກທະນາຄານເທົ່ານັ້ນ", "en": "Bank deposits only"},
           {"lo": "ພັນທະບັດລັດຖະບານ ຫຼື ກອງທຶນຕາສານໜີ້", "en": "Government bonds or bond funds"},
           {"lo": "ຮຸ້ນ ຫຼື ກອງທຶນຮຸ້ນ", "en": "Stocks or equity funds"},
           {"lo": "ຕາສານອະນຸພັນ, ຄຣິບໂຕ ຫຼື ຊັບສິນສ່ຽງສູງອື່ນໆ", "en": "Derivatives, crypto or other high-risk assets"}]},
    {"q": {"lo": "ທ່ານຄາດວ່າຈະບໍ່ຈຳເປັນຕ້ອງໃຊ້ເງິນກ້ອນນີ້ເປັນເວລາດົນປານໃດ?",
           "en": "How long can you leave this money invested without needing it?"},
     "a": [{"lo": "ບໍ່ເກີນ 1 ປີ", "en": "Up to 1 year"},
           {"lo": "1–3 ປີ", "en": "1–3 years"},
           {"lo": "3–5 ປີ", "en": "3–5 years"},
           {"lo": "ຫຼາຍກວ່າ 5 ປີ", "en": "More than 5 years"}]},
    {"q": {"lo": "ເປົ້າໝາຍຫຼັກໃນການລົງທຶນຂອງທ່ານແມ່ນຫຍັງ?", "en": "What is your main goal for investing?"},
     "a": [{"lo": "ຮັກສາເງິນຕົ້ນໃຫ້ປອດໄພ, ຮັບຜົນຕອບແທນໜ້ອຍແຕ່ສະໝ່ຳສະເໝີ", "en": "Keep my money safe, with a small steady return"},
           {"lo": "ຜົນຕອບແທນສະໝ່ຳສະເໝີ, ຍອມເສຍເງິນຕົ້ນໄດ້ບາງສ່ວນ", "en": "A steady return, accepting a small loss of principal"},
           {"lo": "ຜົນຕອບແທນສູງຂຶ້ນ, ຍອມເສຍເງິນຕົ້ນໄດ້ຫຼາຍຂຶ້ນ", "en": "A higher return, accepting a larger loss of principal"},
           {"lo": "ຜົນຕອບແທນສູງສຸດໃນໄລຍະຍາວ, ຍອມຮັບການຂາດທຶນກ້ອນໃຫຍ່ໄດ້", "en": "The highest long-term return, accepting big losses on the way"}]},
    {"q": {"lo": "ຖ້າເລືອກໄດ້ 1 ທາງ, ທ່ານຈະເລືອກການລົງທຶນແບບໃດ (ຜົນໃນ 1 ປີ)?",
           "en": "Which investment would you choose (possible result after 1 year)?"},
     "a": [{"lo": "ດີສຸດໄດ້ກຳໄລ 2.5%, ຮ້າຍສຸດບໍ່ຂາດທຶນ", "en": "Best case +2.5%, worst case no loss"},
           {"lo": "ດີສຸດໄດ້ກຳໄລ 7%, ຮ້າຍສຸດຂາດທຶນ 1%", "en": "Best case +7%, worst case −1%"},
           {"lo": "ດີສຸດໄດ້ກຳໄລ 15%, ຮ້າຍສຸດຂາດທຶນ 5%", "en": "Best case +15%, worst case −5%"},
           {"lo": "ດີສຸດໄດ້ກຳໄລ 25%, ຮ້າຍສຸດຂາດທຶນ 15%", "en": "Best case +25%, worst case −15%"}]},
    {"q": {"lo": "ຖ້າລົງທຶນໃນຊັບສິນທີ່ມີໂອກາດກຳໄລສູງ ແຕ່ກໍ່ມີໂອກາດຂາດທຶນສູງ, ທ່ານຈະຮູ້ສຶກແນວໃດ?",
           "en": "How would you feel holding an asset that can gain a lot but can also lose a lot?"},
     "a": [{"lo": "ກັງວົນ ແລະ ຢ້ານຂາດທຶນ", "en": "Worried and afraid of losing"},
           {"lo": "ບໍ່ສະບາຍໃຈ ແຕ່ພໍເຂົ້າໃຈໄດ້", "en": "Uneasy, but I understand it to a degree"},
           {"lo": "ເຂົ້າໃຈ ແລະ ຮັບຄວາມຜັນຜວນໄດ້ລະດັບໜຶ່ງ", "en": "I understand and can accept the swings"},
           {"lo": "ບໍ່ກັງວົນກັບການຂາດທຶນກ້ອນໃຫຍ່ ເພາະຫວັງຜົນຕອບແທນທີ່ສູງຂຶ້ນ", "en": "Not worried about big losses — I want the higher return"}]},
    {"q": {"lo": "ທ່ານຈະເລີ່ມກັງວົນ ຫຼື ຮັບບໍ່ໄດ້ ເມື່ອມູນຄ່າເງິນລົງທຶນຫຼຸດລົງເທົ່າໃດ?",
           "en": "At what fall in value would you start to feel you cannot accept it?"},
     "a": [{"lo": "5% ຫຼື ໜ້ອຍກວ່າ", "en": "5% or less"},
           {"lo": "ຫຼາຍກວ່າ 5% ຫາ 10%", "en": "More than 5% up to 10%"},
           {"lo": "ຫຼາຍກວ່າ 10% ຫາ 20%", "en": "More than 10% up to 20%"},
           {"lo": "ຫຼາຍກວ່າ 20%", "en": "More than 20%"}]},
    {"q": {"lo": "ປີກາຍທ່ານລົງທຶນ 100,000 ແລະ ປີນີ້ມູນຄ່າເຫຼືອ 85,000. ທ່ານຈະເຮັດແນວໃດ?",
           "en": "Last year you invested 100,000 and it is now worth 85,000. What do you do?"},
     "a": [{"lo": "ຕົກໃຈ ແລະ ຂາຍທັງໝົດ", "en": "Panic and sell everything"},
           {"lo": "ກັງວົນ ແລະ ຍ້າຍບາງສ່ວນໄປຊັບສິນທີ່ສ່ຽງໜ້ອຍກວ່າ", "en": "Worry and move part of it into safer assets"},
           {"lo": "ຖືຕໍ່ ແລະ ລໍຖ້າໃຫ້ລາຄາກັບຄືນ", "en": "Hold on and wait for it to recover"},
           {"lo": "ໝັ້ນໃຈ ແລະ ຊື້ເພີ່ມເພື່ອສະເລ່ຍຕົ້ນທຶນ", "en": "Stay confident and buy more at the lower price"}]},
]

MIN_SCORE, MAX_SCORE = len(QUESTIONS), len(QUESTIONS) * 4

# ประเภทสินทรัพย์ (เรียงจากเสี่ยงต่ำ → สูง)
ASSETS = [
    ("cash",   {"lo": "ເງິນຝາກ ແລະ ຕາສານໜີ້ໄລຍະສັ້ນ", "en": "Deposits and short-term bonds"}),
    ("bonds",  {"lo": "ພັນທະບັດ ແລະ ຮຸ້ນກູ້", "en": "Government and corporate bonds"}),
    ("stocks", {"lo": "ຮຸ້ນ", "en": "Stocks"}),
    ("alt",    {"lo": "ຊັບສິນທາງເລືອກ (ຄຳ, ອະສັງຫາລິມະຊັບ)", "en": "Alternatives (gold, property)"}),
]

# ระดับผู้ลงทุน: (คะแนนสูงสุดของระดับ, ชื่อ, คำอธิบาย, สัดส่วน % ตามลำดับ ASSETS)
LEVELS = [
    {"max": 14, "name": {"lo": "ຮັບຄວາມສ່ຽງໄດ້ຕ່ຳ", "en": "Conservative"},
     "desc": {"lo": "ເນັ້ນຮັກສາເງິນຕົ້ນ. ຮັບການຂາດທຶນໄດ້ໜ້ອຍຫຼາຍ ແລະ ຕ້ອງການຜົນຕອບແທນທີ່ສະໝ່ຳສະເໝີ.",
              "en": "Protecting your money comes first. You can accept very little loss and want a steady return."},
     "mix": [60, 30, 10, 0]},
    {"max": 21, "name": {"lo": "ຮັບຄວາມສ່ຽງໄດ້ປານກາງຄ່ອນຂ້າງຕ່ຳ", "en": "Moderately conservative"},
     "desc": {"lo": "ຮັບການຂາດທຶນໄດ້ໜ້ອຍ. ຕ້ອງການລາຍຮັບສະໝ່ຳສະເໝີ ໂດຍມີຮຸ້ນບາງສ່ວນເພື່ອການເຕີບໂຕ.",
              "en": "You can accept small losses. You want steady income, with some stocks for growth."},
     "mix": [30, 40, 25, 5]},
    {"max": 29, "name": {"lo": "ຮັບຄວາມສ່ຽງໄດ້ປານກາງຄ່ອນຂ້າງສູງ", "en": "Balanced"},
     "desc": {"lo": "ຮັບມູນຄ່າທີ່ຫຼຸດລົງເປັນບາງຄັ້ງໄດ້ ເພື່ອແລກກັບຜົນຕອບແທນໄລຍະຍາວທີ່ດີຂຶ້ນ.",
              "en": "You can live with falls in value from time to time in exchange for a better long-term return."},
     "mix": [15, 35, 40, 10]},
    {"max": 36, "name": {"lo": "ຮັບຄວາມສ່ຽງໄດ້ສູງ", "en": "Growth"},
     "desc": {"lo": "ຮັບຄວາມຜັນຜວນສູງ ແລະ ການຂາດທຶນພໍສົມຄວນໄດ້. ເນັ້ນການເຕີບໂຕຂອງເງິນລົງທຶນໄລຍະຍາວ.",
              "en": "You accept large swings and meaningful losses. Long-term growth is the priority."},
     "mix": [10, 20, 60, 10]},
    {"max": MAX_SCORE, "name": {"lo": "ຮັບຄວາມສ່ຽງໄດ້ສູງຫຼາຍ", "en": "Aggressive"},
     "desc": {"lo": "ຕ້ອງການຜົນຕອບແທນສູງສຸດ ແລະ ຮັບການຂາດທຶນກ້ອນໃຫຍ່ໄດ້ ໂດຍບໍ່ຕ້ອງໃຊ້ເງິນກ້ອນນີ້ໃນໄລຍະໃກ້.",
              "en": "You want the highest return and can absorb big losses, with no near-term need for this money."},
     "mix": [5, 10, 75, 10]},
]


def score(answers: list) -> dict:
    """answers = ลำดับตัวเลือกที่ตอบ (0–3) ของแต่ละข้อ → {"score": คะแนนรวม, "level": ระดับ 1–5}"""
    total = sum(a + 1 for a in answers)
    level = next(i for i, lv in enumerate(LEVELS, 1) if total <= lv["max"])
    return {"score": total, "level": level}


def save(user_id: int, answers: list) -> dict:
    """บันทึกผลลงฐานข้อมูล (เก็บทุกครั้งที่ทำ เพื่อดูย้อนหลังได้)"""
    result = score(answers)
    with auth.get_conn() as conn:
        conn.execute(
            "INSERT INTO risk_profiles (user_id, score, level, answers_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, result["score"], result["level"], json.dumps(answers), datetime.now().isoformat()),
        )
    return result


def load(user_id: int):
    """อ่านผลล่าสุดของผู้ใช้ → dict หรือ None ถ้ายังไม่เคยทำ"""
    with auth.get_conn() as conn:
        row = conn.execute(
            "SELECT score, level, answers_json, created_at FROM risk_profiles "
            "WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,),
        ).fetchone()
    if not row:
        return None
    return {"score": row[0], "level": row[1], "answers": json.loads(row[2]), "created_at": row[3]}
