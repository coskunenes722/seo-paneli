import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- 2. VERİTABANI KURULUMU ---
def init_db():
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS icerikler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, marka TEXT, konu TEXT, icerik TEXT, tarih TEXT, tip TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS skorlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, marka TEXT, puan INTEGER, tarih TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. YARDIMCI FONKSİYONLAR ---
def icerik_kaydet(kullanici, marka, konu, icerik, tip="Makale"):
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO icerikler (kullanici, marka, konu, icerik, tarih, tip) VALUES (?, ?, ?, ?, ?, ?)",
              (kullanici, marka, konu, icerik, tarih, tip))
    conn.commit()
    conn.close()

# --- 4. API YAPILANDIRMASI ---
# DİKKAT: Anahtarı tek satırda yazın ve tırnakla kapatın!
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# --- 5. ZEKA FONKSİYONLARI ---
def analiz_yap(marka, sektor):
    try:
        p_prompt = f"'{marka}' markasının '{sektor}' pazarındaki küresel AI bilinirlik puanını (0-100) sadece rakam olarak ver."
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))
        y_prompt = f"{marka} ({sektor}) için 3 maddelik stratejik özet yaz."
        yorum = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": y_prompt}]).choices[0].message.content
        return puan, yorum
    except: return 50, "Analiz başarısız. API anahtarını kontrol edin."

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("🚀 Admin Panel")
    marka_adi = st.text_input("Markanız", "Coca Cola")
    sektor_adi = st.text_input("Sektör", "İçecek")
    
    if "aktif_marka" not in st.session_state or st.session_state["aktif_marka"] != marka_adi:
        st.session_state["aktif_marka"] = marka_adi
        st.session_state["puan"], st.session_state["yorum"] = None, None

    st.divider()
    nav = st.radio("Sistem Menüsü", ["📊 Dashboard", "✍️ İçerik Üretimi", "📜 Arşiv"])

# --- 7. DASHBOARD MODÜLÜ ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center;'>🚀 {marka_adi} Operasyon Merkezi</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True) or st.session_state["puan"] is None:
        with st.spinner("Veriler analiz ediliyor..."):
            p, y = analiz_yap(marka_adi, sektor_adi)
            st.session_state["puan"], st.session_state["yorum"] = p, y
            conn = sqlite3.connect('arsiv.db')
            conn.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka_adi, p, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            st.rerun()

    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"], title={'text': "AI Skoru"},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"},
                               'steps': [{'range': [0, 50], 'color': '#FECACA'}, {'range': [50, 100], 'color': '#BBF7D0'}]}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🤖 Stratejik Analiz")
        st.success(st.session_state["yorum"])

# --- 8. İÇERİK ÜRETİMİ MODÜLÜ ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik Fabrikası")
    topic = st.text_input("📝 Ana Konu Başlığı", placeholder="Örn: Coca Cola Pazarlama Stratejisi")
    
    if st.button("🌟 Tüm İçerik Paketini Hazırla", use_container_width=True):
        if not topic: st.error("Lütfen bir konu başlığı girin!")
        else:
            with st.spinner("İçerikler hazırlanıyor..."):
                prompt = f"Konu: {topic}. Lütfen [BLOG_B]...[BLOG_S], [SOSYAL_B]...[SOSYAL_S] etiketleriyle yaz."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                
                def parse(tag):
                    m = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", res, re.DOTALL)
                    return m.group(1).strip() if m else ""

                t1, t2 = st.tabs(["📝 Blog", "📱 Sosyal Medya"])
                with t1: st.markdown(parse("BLOG") if parse("BLOG") else res)
                with t2: st.markdown(parse("SOSYAL"))
                icerik_kaydet("admin", marka_adi, topic, res, tip="Tam Paket")