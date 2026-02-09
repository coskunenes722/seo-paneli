import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime  # Hatayı çözen kritik kütüphane

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- VERİTABANI ---
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

# --- GİRİŞ SİSTEMİ ---
KULLANICILAR = {"admin": "12345", "ahmet_bey": "ahmet123"}
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False

if not st.session_state["giris_yapildi"]:
    st.title("🔐 VetraPos AI Ultimate")
    k = st.text_input("Kullanıcı")
    s = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if k in KULLANICILAR and KULLANICILAR[k] == s:
            st.session_state["giris_yapildi"] = True
            st.session_state["aktif_kullanici"] = k
            st.rerun()
    st.stop()

# --- API ---
api_key = "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" 
client = OpenAI(api_key=api_key)

# --- AI FONKSİYONLARI ---
def get_canli_skor(marka, sektor):
    prompt = f"""
    Sen dijital bir denetçisin. '{marka}' markasını '{sektor}' sektöründe AI görünürlüğü açısından analiz et.
    Coca-Cola gibi dev markalar 85-95 arası, VetraPos gibi yeni girişimler 20-45 arası puan almalı.
    SADECE rakam ver (Örn: 72).
    """
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.8).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, res)))
        tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka, puan, tarih))
        conn.commit()
        conn.close()
        return puan
    except:
        return 50

def get_marka_yorumu(marka, sektor):
    prompt = f"Yapay zeka modelleri şu an {marka} markasını {sektor} sektöründe nasıl görüyor? 3 maddelik özet ver."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content

# --- ARAYÜZ ---
with st.sidebar:
    st.title(f"👋 {st.session_state['aktif_kullanici']}")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📜 Arşiv"])
    if st.button("Güvenli Çıkış"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

# --- DASHBOARD ---
if nav == "📊 Dashboard":
    st.title(f"📊 {marka_adi} Performans Dashboard")
    with st.spinner("Analiz ediliyor..."):
        puan = get_canli_skor(marka_adi, sektor_adi)
        yorum = get_marka_yorumu(marka_adi, sektor_adi)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = puan,
            title = {'text': "AI Bilinirlik Skoru"},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"},
                     'steps' : [{'range': [0, 40], 'color': "red"}, {'range': [70, 100], 'color': "green"}]}))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("🤖 Yapay Zeka Raporu")
        st.success(yorum)

    st.divider()
    st.subheader("📈 Skor Gelişim Trendi")
    conn = sqlite3.connect('arsiv.db')
    df = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    conn.close()
    if not df.empty: st.line_chart(df.set_index('tarih'))

# --- DİĞER SEKMEER ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Analizi")
    r_url = st.text_input("Rakip URL")
    if st.button("Analiz Et"):
        st.info("Rakip stratejisi hazırlanıyor...")
        # Analiz fonksiyonu buraya gelecek

elif nav == "✍️ İçerik Üretimi":
    st.title("✍️ İçerik Fabrikası")
    konu = st.text_input("Konu nedir?")
    if st.button("Makale Yaz"):
        st.write("Makale hazırlanıyor...")