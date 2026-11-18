# =====================================================
# quiz.py — หน้า "แบบประเมินผู้ลงทุน"
# 3 สถานะ:
#   intro   หน้าแนะนำ (ยังไม่เคยทำ)
#   run     ตอบคำถามทีละข้อ มีแถบความคืบหน้า + ปุ่มย้อนกลับ/ถัดไป
#   result  ผลประเมิน: คะแนน, ระดับ, สัดส่วนการลงทุนที่แนะนำ, คำตอบที่เลือก
# คำถามและการให้คะแนนอยู่ใน core/quiz.py
# =====================================================
import streamlit as st

from core import quiz, theme
from core.i18n import t
from core.ui import esc, goto, keep, md, tile

N = len(quiz.QUESTIONS)


def _lang():
    return st.session_state.get("lang", "lo")


# ---------- ปุ่มควบคุม (callback) ----------
def _start():
    st.session_state.quiz_mode = "run"
    st.session_state.quiz_step = 0
    st.session_state.quiz_answers = {}


def _cancel():
    """เลิกทำกลางคัน → กลับไปหน้าผลเดิม (ถ้าเคยทำ) หรือหน้าแนะนำ"""
    st.session_state.pop("quiz_mode", None)


def _back():
    st.session_state.quiz_step = max(0, st.session_state.quiz_step - 1)


def _next():
    step = st.session_state.quiz_step
    choice = st.session_state.get(f"quiz_q{step}")
    if choice is None:
        return
    st.session_state.quiz_answers[step] = choice
    if step + 1 < N:
        st.session_state.quiz_step = step + 1
    else:                                         # ตอบครบแล้ว → บันทึกผล
        answers = [st.session_state.quiz_answers[i] for i in range(N)]
        quiz.save(st.session_state.user["id"], answers)
        st.session_state.quiz_mode = "result"


# ---------- หน้าแนะนำ ----------
def _intro():
    left, right = st.columns([3, 2])
    with left, st.container(key="cardblue_quizintro"):
        md(f'<div class="card-title" style="font-size:1.25rem">{t("qz_intro_title")}</div>'
           f'<p style="margin:.4rem 0 .8rem">{t("qz_intro_body")}</p>'
           f'<span class="chip">{t("qz_chip_q").format(n=N)}</span>'
           f'<span class="chip">{t("qz_chip_time")}</span>'
           f'<span class="chip">{t("qz_chip_save")}</span>')
        st.write("")
        st.button(t("qz_start"), type="primary", on_click=_start)
    with right, st.container(key="card_quizwhy"):
        md(f'<div class="card-title">{t("qz_why_title")}</div>'
           f'<p class="muted" style="margin-top:.3rem">{t("qz_why_body")}</p>')


# ---------- ตอบคำถามทีละข้อ ----------
def _run():
    lang = _lang()
    step = st.session_state.quiz_step
    item = quiz.QUESTIONS[step]
    _, mid, _ = st.columns([1, 4, 1])
    with mid:
        md(f'<div class="eyebrow">{t("qz_progress").format(i=step + 1, n=N)}</div>'
           f'<div class="meter" style="margin:.4rem 0 1rem"><i style="width:{(step + 1) / N * 100:.0f}%;background:var(--accent)"></i></div>')
        with st.container(key="card_quizq"):
            md(f'<div class="quiz-q">{esc(item["q"][lang])}</div>')
            with st.container(key="quizopt"):
                # ค่าเริ่มต้น = คำตอบที่เคยเลือกไว้ (กรณีกดย้อนกลับ) และจำไว้แม้สลับภาษา
                keep(f"quiz_q{step}", st.session_state.quiz_answers.get(step))
                choice = st.radio(
                    item["q"][lang], range(4), key=f"quiz_q{step}",
                    format_func=lambda i: item["a"][i][lang], label_visibility="collapsed",
                )
        b1, b_mid, b2 = st.columns([1, 2, 1])
        if step > 0:
            b1.button(t("qz_back"), on_click=_back, width="stretch")
        else:
            b1.button(t("qz_cancel"), on_click=_cancel, width="stretch")
        b2.button(t("qz_finish") if step == N - 1 else t("qz_next"), type="primary",
                  on_click=_next, disabled=choice is None, width="stretch")


# ---------- ผลประเมิน ----------
def _allocation(level_info):
    """สัดส่วนการลงทุนที่แนะนำ: แถบแบ่งส่วน 1 แถบ + รายการกำกับ (ไม่ใช้สีอย่างเดียว มีชื่อและ % ทุกส่วน)"""
    c = theme.tokens()
    lang = _lang()
    colors = [c["accent"], c["series2"], c["series3"], c["series4"]]
    bar = rows = ""
    for (_, name), share, color in zip(quiz.ASSETS, level_info["mix"], colors):
        label = esc(name[lang])
        if share > 0:
            bar += f'<i style="width:{share}%;background:{color}" title="{label}: {share}%"></i>'
        rows += (f'<div class="alloc-row"><span class="sw" style="background:{color}"></span>'
                 f'<span>{label}</span><b>{share}%</b></div>')
    md(f'<div class="card-title">{t("qz_alloc_title")}</div><div class="muted">{t("qz_alloc_sub")}</div>'
       f'<div class="alloc-bar">{bar}</div>{rows}')


def _result(profile):
    lang = _lang()
    level = profile["level"]
    info = quiz.LEVELS[level - 1]
    span = quiz.MAX_SCORE - quiz.MIN_SCORE

    c1, c2 = st.columns([1, 2])
    with c1, st.container(key="cardblue_quizscore"):
        tile(t("qz_score"), f'{profile["score"]} <small>/ {quiz.MAX_SCORE}</small>',
             t("qz_done_on").format(d=profile["created_at"][:10]),
             meter=(profile["score"] - quiz.MIN_SCORE) / span)
    with c2, st.container(key="cardlav_quizlevel"):
        steps = "".join(f'<i class="{"on" if i <= level else ""}"></i>' for i in range(1, 6))
        md(f'<div class="tile"><div class="label">{t("qz_level").format(i=level)}</div>'
           f'<div class="value" style="font-size:1.45rem">{esc(info["name"][lang])}</div>'
           f'<div class="levels">{steps}</div>'
           f'<div class="sub" style="opacity:.85">{esc(info["desc"][lang])}</div></div>')

    left, right = st.columns([3, 2])
    with left, st.container(key="card_quizalloc"):
        _allocation(info)
    with right, st.container(key="cardcta_quiznext"):
        md(f'<h3 style="margin:0 0 .3rem">{t("qz_next_title")}</h3><p class="muted">{t("qz_next_body")}</p>')
        st.button(t("qz_to_portfolio"), key="quiz_to_port", on_click=goto, args=("page_portfolio",))

    with st.expander(t("qz_answers")):
        body = "".join(
            f'<tr><td>{i + 1}. {esc(q["q"][lang])}<div class="co">{esc(q["a"][a][lang])}</div></td><td>{a + 1}</td></tr>'
            for i, (q, a) in enumerate(zip(quiz.QUESTIONS, profile["answers"])))
        md(f'<div class="tbl-wrap"><table class="tbl"><thead><tr><th>{t("qz_col_q")}</th>'
           f'<th>{t("qz_col_pts")}</th></tr></thead><tbody>{body}</tbody></table></div>')
    with st.expander(t("method")):
        bands, low = "", quiz.MIN_SCORE
        for i, lv in enumerate(quiz.LEVELS, 1):
            bands += f"- {low}–{lv['max']}: **{lv['name'][lang]}**\n"
            low = lv["max"] + 1
        st.markdown(t("qz_method").format(n=N, lo=quiz.MIN_SCORE, hi=quiz.MAX_SCORE) + "\n\n" + bands)

    st.button(t("qz_retake"), on_click=_start)


# ---------- หน้าหลักของไฟล์นี้ ----------
def render():
    st.title(t("page_quiz"))
    profile = quiz.load(st.session_state.user["id"])
    # เข้าหน้านี้ครั้งแรกในรอบการใช้งาน: เคยทำแล้ว → แสดงผล, ยังไม่เคย → หน้าแนะนำ
    mode = st.session_state.setdefault("quiz_mode", "result" if profile else "intro")
    if mode == "run":
        _run()
    elif mode == "result" and profile:
        _result(profile)
    else:
        _intro()
    md(f'<p class="muted" style="margin-top:1.2rem">⚠️ {t("disclaimer")}</p>')
