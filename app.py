import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re # Metin parçalama için kritik kütüphane

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

# --- YARDIMCI FONKSİYONLAR ---
def icerik_kaydet(kullanici, marka, konu, icerik, tip="Makale"):
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO icerikler (kullanici, marka, konu, icerik, tarih, tip) VALUES (?, ?, ?, ?, ?, ?)",
              (kullanici, marka, konu, icerik, tarih, tip))
    conn.commit()
    conn.close()

# --- API ---
api_key = "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" 
client = OpenAI(api_key=api_key)

# --- ARAYÜZ ---
with st.sidebar:
    st.title("👋 Admin")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    # Emojili nav seçimi, SyntaxError almamak için metinle eşleşmeli
    nav = st.radio("Menü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📜 Arşiv"])

# --- 1. DASHBOARD ---
if nav == "📊 Dashboard":
    st.title("📊 Marka Görünürlük Dashboard")
    st.info(f"{marka_adi} markası için güncel veriler hazırlanıyor...")

# --- 2. RAKİP TARAYICI ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Site Tarayıcı")
    r_url = st.text_input("Rakip URL")

# --- 3. İÇERİK ÜRETİMİ (TAM DOLU SEKMELER) ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik & Görsel Fabrikası")
    
    with st.container():
        c1, c2 = st.columns([2, 1])
        with c1:
            topic = st.text_input("📝 Ana Konu Başlığı", placeholder="Örn: Restoranlar için sanal pos avantajları")
        with c2:
            target_tone = st.selectbox("🎭 İçerik Üslubu", ["Kurumsal", "Samimi", "Teknik"])
    
    gen_image = st.toggle("🖼️ Yapay Zeka Görseli Üret (DALL-E 3)", value=True)
    st.divider()

    if st.button("🌟 Tüm İçerik Paketini Hazırla", use_container_width=True):
        if not topic:
            st.error("Lütfen bir konu başlığı girin!")
        else:
            with st.spinner("AI fabrikanız tüm sekmeleri dolduruyor..."):
                # 1. Metin Üretimi (Özel etiketlerle)
                prompt = f"""
                Konu: {topic}
                Marka: {marka_adi}
                Üslup: {target_tone}
                Lütfen içeriği tam olarak şu etiketler arasına yaz:
                [BLOG_B] ... [BLOG_S]
                [SOSYAL_B] ... [SOSYAL_S]
                [BULTEN_B] ... [BULTEN_S]
                [VIDEO_B] ... [VIDEO_S]
                """
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                
                # 2. Görsel Üretimi
                img_url = None
                if gen_image:
                    try:
                        img_res = client.images.generate(model="dall-e-3", prompt=f"Modern marketing visual for: {topic}", n=1)
                        img_url = img_res.data[0].url
                    except: st.warning("Görsel üretilemedi.")

                # 3. Metin Parçalama (Regex)
                def parse_it(tag):
                    match = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", response, re.DOTALL)
                    return match.group(1).strip() if match else ""

                blog_txt = parse_it("BLOG")
                sosyal_txt = parse_it("SOSYAL")
                bulten_txt = parse_it("BULTEN")
                video_txt = parse_it("VIDEO")

                # 4. SEKMELİ GÖRÜNÜM
                tab1, tab2, tab3, tab4 = st.tabs(["📝 Blog & SEO", "📱 Sosyal Medya", "📧 E-Bülten", "🎬 Video/Reels"])
                
                with tab1:
                    if img_url: st.image(img_url, caption=topic)
                    st.markdown(blog_txt if blog_txt else response)
                    icerik_kaydet("admin", marka_adi, topic, blog_txt if blog_txt else response, tip="Blog")

                with tab2:
                    st.subheader("📱 Sosyal Medya Kanalları")
                    st.markdown(sosyal_txt if sosyal_txt else "İçerik ayrıştırılamadı.")

                with tab3:
                    st.subheader("📧 Haftalık Bülten Taslağı")
                    st.markdown(bulten_txt if bulten_txt else "İçerik ayrıştırılamadı.")

                with tab4:
                    st.subheader("🎬 Kısa Video Senaryosu")
                    st.markdown(video_txt if video_txt else "İçerik ayrıştırılamadı.")

# --- 4. ARŞİV ---
elif nav == "📜 Arşiv":
    st.title("📜 İçerik Arşivi")