import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime

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

# --- GİRİŞ SİSTEMİ ---
KULLANICILAR = {"admin": "12345", "ahmet_bey": "ahmet123"}
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False

if not st.session_state["giris_yapildi"]:
    st.title("🔐 VetraPos AI Pro Giriş")
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

# --- ZEKA FONKSİYONLARI ---
def get_canli_skor(marka, sektor):
    try:
        prompt = f"{marka} ({sektor}) için AI bilinirlik puanı ver (Sadece rakam)."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, res)))
        tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka, puan, tarih))
        conn.commit()
        conn.close()
        return puan
    except: return 50

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

# --- 1. DASHBOARD ---
if nav == "📊 Dashboard":
    st.title("📊 Marka Görünürlük Dashboard")
    puan = get_canli_skor(marka_adi, sektor_adi)
    st.metric("AI Bilinirlik Skoru", f"{puan}/100")
    conn = sqlite3.connect('arsiv.db')
    df = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}'", conn)
    if not df.empty: st.line_chart(df.set_index('tarih'))
    conn.close()

# --- 2. RAKİP TARAYICI ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Site Tarayıcı")
    r_url = st.text_input("Rakip URL")
    if st.button("Analiz Et"):
        st.info(f"{r_url} analiz ediliyor...")

# --- 3. İÇERİK ÜRETİMİ (HATASIZ VERSİYON) ---
elif nav == "✍️ İçerik Üretimi":
    st.title("✍️ 360° İçerik & Görsel Fabrikası")
    
    with st.expander("📝 İçerik Ayarları", expanded=True):
        topic = st.text_input("Konu Başlığı", placeholder="Örn: Sanal POS Avantajları")
        gen_image = st.checkbox("🖼️ Görsel Üret (DALL-E 3)", value=True)

    if st.button("🚀 Tüm İçerik Paketini Hazırla"):
        if not topic:
            st.error("Lütfen bir konu başlığı girin!")
        else:
            with st.spinner("İçerikler üretiliyor..."):
                # AI'dan ayrıştırılabilir formatta cevap iste
                prompt = f"""
                Konu: {topic}
                Lütfen şu formatta yaz:
                ###BLOG### (Makale buraya)
                ###SOSYAL### (Sosyal medya postları buraya)
                ###BULTEN### (E-bülten buraya)
                ###VIDEO### (Reels senaryosu buraya)
                """
                full_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                
                # Görsel Üretimi
                img_url = None
                if gen_image:
                    try:
                        img_res = client.images.generate(model="dall-e-3", prompt=f"Professional photo for: {topic}", n=1)
                        img_url = img_res.data[0].url
                    except: pass

                # İçeriği parçala
                parts = full_res.split("###")
                blog, sosyal, bulten, video = "", "", "", ""
                for p in parts:
                    if "BLOG" in p: blog = p.replace("BLOG", "").strip()
                    if "SOSYAL" in p: sosyal = p.replace("SOSYAL", "").strip()
                    if "BULTEN" in p: bulten = p.replace("BULTEN", "").strip()
                    if "VIDEO" in p: video = p.replace("VIDEO", "").strip()

                tab1, tab2, tab3, tab4 = st.tabs(["📝 Blog", "📱 Sosyal Medya", "📧 E-Bülten", "🎬 Video/Reels"])
                with tab1:
                    if img_url: st.image(img_url)
                    st.markdown(blog if blog else full_res)
                    icerik_kaydet(st.session_state["aktif_kullanici"], marka_adi, topic, full_res, tip="Tam Paket")
                with tab2: st.write(sosyal)
                with tab3: st.write(bulten)
                with tab4: st.write(video)

# --- 4. ARŞİV ---
elif nav == "📜 Arşiv":
    st.title("📜 İçerik Arşivi")
    conn = sqlite3.connect('arsiv.db')
    df_arsiv = pd.read_sql("SELECT tarih, konu, icerik FROM icerikler ORDER BY id DESC", conn)
    for i, row in df_arsiv.iterrows():
        with st.expander(f"{row['tarih']} | {row['konu']}"): st.markdown(row['icerik'])
    conn.close()