import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re
import requests

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- API YAPILANDIRMASI ---
OPENAI_KEY = "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"
SERPAPI_KEY = "BURAYA_SERPAPI_KEY_YAZIN" # Gerçek Google verileri için (Opsiyonel)

client = OpenAI(api_key=OPENAI_KEY)

# --- VERİTABANI VE İLK KURULUM ---
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

def get_canli_skor(marka, sektor):
    # Gerçekçi puanlama: Marka bilinirliğine göre mantıksal analiz
    prompt = f"'{marka}' markasının '{sektor}' sektöründeki dijital varlığını 0-100 arası puanla. Sadece rakam ver."
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], timeout=10).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, res)))
        tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka, puan, tarih))
        conn.commit()
        conn.close()
        return puan
    except: return 50

def get_marka_yorumu(marka, sektor):
    prompt = f"{marka} ({sektor}) için 3 maddelik stratejik AI pazar özeti yaz."
    try:
        return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
    except: return "Analiz şu an yapılamıyor."

def google_serp_analiz(marka, anahtar_kelime):
    # SerpApi varsa gerçek veri çeker, yoksa AI ile simüle eder
    if SERPAPI_KEY:
        params = {"q": anahtar_kelime, "api_key": SERPAPI_KEY}
        try:
            search_res = requests.get("https://serpapi.com/search", params=params).json()
            # Basit bir sıralama kontrolü (ilk 10 sonuçta var mı?)
            found = False
            for result in search_res.get("organic_results", []):
                if marka.lower() in result["title"].lower() or marka.lower() in result["link"].lower():
                    found = True
                    return f"✅ Markanız '{anahtar_kelime}' kelimesinde ilk sayfa sonuçlarında tespit edildi!"
            if not found: return f"❌ Markanız '{anahtar_kelime}' kelimesinde ilk sayfada henüz yer almıyor."
        except: pass
    
    # AI Simülasyonu
    prompt = f"Google'da '{anahtar_kelime}' araması yapıldığında {marka} markasının çıkma olasılığını analiz et."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content

# --- ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title("👋 Admin Panel")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Sistem Menüsü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📜 Arşiv"])

# --- 1. DASHBOARD (PROFESYONEL & CANLI) ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🚀 {marka_adi} Stratejik Operasyon Merkezi</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True):
        with st.spinner("Anlık pazar taraması yapılıyor..."):
            puan = get_canli_skor(marka_adi, sektor_adi)
            yorum = get_marka_yorumu(marka_adi, sektor_adi)
            
            # Üst Metrik Kartları
            m1, m2, m3 = st.columns(3)
            m1.metric("AI Bilinirlik", f"%{puan}")
            m2.metric("Pazar Durumu", "Analiz Edildi")
            m3.metric("Trend", "Yükseliyor 📈")

            col1, col2 = st.columns([1, 1.2])
            with col1:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=puan, title={'text': "AI Skoru"},
                                gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"},
                                'steps': [{'range': [0, 50], 'color': '#FECACA'}, {'range': [50, 100], 'color': '#BBF7D0'}]}))
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("🤖 Yapay Zeka Strateji Özeti")
                st.success(yorum)

    st.divider()
    st.subheader("🔍 Live Search: Gerçek Zamanlı Google Analizi")
    kw = st.text_input("Hedef Anahtar Kelime", "Sanal pos firmaları")
    if st.button("🔎 Google Sıralamasını Tara"):
        with st.spinner("Google SERP verileri taranıyor..."):
            serp_res = google_serp_analiz(marka_adi, kw)
            st.info(serp_res)

# --- 3. İÇERİK ÜRETİMİ (TAM DOLU SEKMELER) ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik & Görsel Fabrikası")
    topic = st.text_input("📝 Ana Konu Başlığı")
    gen_image = st.toggle("🖼️ Yapay Zeka Görseli Üret (DALL-E 3)", value=True)

    if st.button("🌟 Tüm İçerik Paketini Hazırla", use_container_width=True):
        with st.spinner("AI İçerik ve Görsel üretiliyor..."):
            prompt = f"Konu: {topic}. Lütfen [BLOG_B]...[BLOG_S], [SOSYAL_B]...[SOSYAL_S], [BULTEN_B]...[BULTEN_S] etiketleriyle yaz."
            full_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
            
            img_url = None
            if gen_image:
                try:
                    img_url = client.images.generate(model="dall-e-3", prompt=f"Marketing visual for: {topic}", n=1).data[0].url
                except: pass

            def parse(tag):
                m = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", full_res, re.DOTALL)
                return m.group(1).strip() if m else ""

            tab1, tab2, tab3 = st.tabs(["📝 Blog & SEO", "📱 Sosyal Medya", "📧 E-Bülten"])
            with tab1:
                if img_url: st.image(img_url)
                st.markdown(parse("BLOG") if parse("BLOG") else full_res)
                icerik_kaydet("admin", marka_adi, topic, parse("BLOG"), tip="Blog")
            with tab2: st.markdown(parse("SOSYAL"))
            with tab3: st.markdown(parse("BULTEN"))