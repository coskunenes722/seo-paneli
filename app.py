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

# --- 3. API YAPILANDIRMASI ---
# DİKKAT: Anahtarı tek satırda ve tırnakları kapatarak yazın!
OPENAI_KEY = "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" 
client = OpenAI(api_key=OPENAI_KEY)

# --- 4. ZEKA FONKSİYONLARI ---
def analiz_yap(marka, sektor):
    try:
        # Puan Analizi (Gerçekçi veri çekimi)
        p_prompt = f"'{marka}' markasının '{sektor}' sektöründeki küresel AI bilinirlik puanını (0-100) sadece rakam olarak ver."
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))
        
        # Stratejik Özet
        y_prompt = f"{marka} markasının {sektor} sektöründeki konumu hakkında 3 maddelik çok kısa stratejik analiz yaz."
        yorum = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": y_prompt}]).choices[0].message.content
        
        return puan, yorum
    except Exception as e:
        # Hata durumunda teknik bilgi verir
        return 50, f"Hata: {str(e)}. Lütfen API anahtarını kontrol edin."

# --- 5. SIDEBAR (DİNAMİK MARKA YÖNETİMİ) ---
with st.sidebar:
    st.title("🚀 Admin Panel")
    marka_adi = st.text_input("Markanız", "Coca Cola")
    sektor_adi = st.text_input("Sektör", "İçecek")
    
    # Marka değiştiğinde verileri sıfırla (Donmayı engeller)
    if "aktif_marka" not in st.session_state or st.session_state["aktif_marka"] != marka_adi:
        st.session_state["aktif_marka"] = marka_adi
        st.session_state["puan"] = None
        st.session_state["yorum"] = None

    st.divider()
    nav = st.radio("Sistem Menüsü", ["📊 Dashboard", "✍️ İçerik Üretimi", "📜 Arşiv"])

# --- 6. DASHBOARD (CANLI ANALİZ MERKEZİ) ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🚀 {marka_adi} Operasyon Merkezi</h1>", unsafe_allow_html=True)
    
    # Veri yoksa veya butona basıldıysa canlı veri çek
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True) or st.session_state["puan"] is None:
        with st.spinner(f"{marka_adi} analiz ediliyor..."):
            p, y = analiz_yap(marka_adi, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["yorum"] = y
            # Veritabanına kaydet
            conn = sqlite3.connect('arsiv.db')
            conn.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", 
                         (marka_adi, p, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            st.rerun()

    # Dashboard Görselleştirme
    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"], 
                        title={'text': "AI Skoru", 'font': {'size': 24}},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"},
                               'steps': [{'range': [0, 60], 'color': '#FECACA'}, {'range': [60, 100], 'color': '#BBF7D0'}]}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🤖 Stratejik Analiz Özeti")
        st.success(st.session_state["yorum"])

    st.divider()
    st.subheader("📈 Skor Gelişim Trendi")
    conn = sqlite3.connect('arsiv.db')
    df_trend = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    if not df_trend.empty:
        st.area_chart(df_trend.set_index('tarih'), color="#3B82F6")
    conn.close()