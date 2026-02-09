import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- VERİTABANI HAZIRLIĞI ---
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

# --- YARDIMCI FONKSİYONLAR ---
def icerik_kaydet(kullanici, marka, konu, icerik, tip="Makale"):
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO icerikler (kullanici, marka, konu, icerik, tarih, tip) VALUES (?, ?, ?, ?, ?, ?)",
              (kullanici, marka, konu, icerik, tarih, tip))
    conn.commit()
    conn.close()

# --- API YAPILANDIRMASI ---
api_key = "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" 
client = OpenAI(api_key=api_key)

# --- ZEKA FONKSİYONLARI (DONMAYI ENGELLEYEN YAPI) ---
def get_canli_skor(marka, sektor):
    try:
        prompt = f"{marka} ({sektor}) için AI skorunu sadece rakam ver (0-100)."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], timeout=10).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, res)))
        return puan
    except:
        return 50

def get_marka_yorumu(marka, sektor):
    try:
        prompt = f"{marka} markasının {sektor} sektöründeki AI durumu hakkında 2 cümlelik özet ver."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], timeout=10).choices[0].message.content
        return res
    except:
        return "Veriler şu an analiz edilemiyor."

# --- ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title("👋 Admin Panel")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Sistem Menüsü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📜 Arşiv"])

# --- 1. DASHBOARD ---
if nav == "📊 Dashboard":
    st.title("📊 Marka Görünürlük Dashboard")
    
    # Donmayı engellemek için butonla tetikleme veya statik gösterim
    if st.button("🔄 Verileri Güncelle"):
        with st.spinner("AI Analizi yapılıyor..."):
            puan = get_canli_skor(marka_adi, sektor_adi)
            yorum = get_marka_yorumu(marka_adi, sektor_adi)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=puan, title={'text': "AI Skoru"},
                                gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"}}))
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("🤖 AI Özeti")
                st.success(yorum)
    else:
        st.info("Lütfen verileri çekmek için yukarıdaki butona basın.")

# --- 3. İÇERİK ÜRETİMİ (TAM DOLU SEKMELER) ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik & Görsel Fabrikası")
    topic = st.text_input("📝 Ana Konu Başlığı")
    gen_image = st.toggle("🖼️ Görsel Üret (DALL-E 3)", value=True)

    if st.button("🌟 Tüm İçerik Paketini Hazırla"):
        if not topic:
            st.error("Konu girin!")
        else:
            with st.spinner("İçerikler sekmelere dağıtılıyor..."):
                prompt = f"Konu: {topic}. Lütfen [BLOG_B]...[BLOG_S], [SOSYAL_B]...[SOSYAL_S], [BULTEN_B]...[BULTEN_S] etiketleriyle yaz."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                
                # Regex ile parçalama
                def parse(tag):
                    m = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", res, re.DOTALL)
                    return m.group(1).strip() if m else ""

                t1, t2, t3 = st.tabs(["📝 Blog", "📱 Sosyal", "📧 Bülten"])
                with t1: st.markdown(parse("BLOG") if parse("BLOG") else res)
                with t2: st.markdown(parse("SOSYAL"))
                with t3: st.markdown(parse("BULTEN"))
                icerik_kaydet("admin", marka_adi, topic, res, tip="Tam Paket")