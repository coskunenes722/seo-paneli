import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- VERİTABANI MİMARİSİ ---
def init_db():
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    # Tabloyu yeni sütunlarla birlikte oluşturur
    c.execute('''CREATE TABLE IF NOT EXISTS icerikler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  kullanici TEXT, marka TEXT, konu TEXT, icerik TEXT, tarih TEXT, tip TEXT)''')
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

# --- API YAPILANDIRMASI ---
api_key = "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" 
client = OpenAI(api_key=api_key)

# --- DASHBOARD SKOR FONKSİYONU ---
def get_canli_skor(marka, sektor):
    try:
        prompt = f"{marka} markasının {sektor} sektöründeki AI puanını ver (Sadece rakam)."
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

# --- ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title(f"👋 {st.session_state['aktif_kullanici']}")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📜 Arşiv"])
    if st.button("Güvenli Çıkış"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

# --- ZEKA FONKSİYONLARI (Eksik fonksiyonlar eklendi) ---

def get_marka_yorumu(marka, sektor):
    # Bu fonksiyon Dashboard'daki analiz özetini üretir
    prompt = f"Yapay zeka modelleri şu an {marka} markasını {sektor} sektöründe nasıl görüyor? 3 maddelik kısa bir stratejik özet ver."
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        return res
    except:
        return "Analiz şu an yapılamıyor, lütfen daha sonra tekrar deneyin."

def get_canli_skor(marka, sektor):
    try:
        prompt = f"{marka} markasının {sektor} sektöründeki AI görünürlük puanını (0-100) sadece rakam olarak ver."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
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

# --- 1. DASHBOARD (PROFESYONEL VERSİYON) ---
if nav == "📊 Dashboard":
    st.title(f"📊 {marka_adi} Stratejik Performans Paneli")
    
    with st.spinner("AI verileri analiz ediliyor..."):
        puan = get_canli_skor(marka_adi, sektor_adi)
        yorum = get_marka_yorumu(marka_adi, sektor_adi)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Profesyonel Hız Göstergesi (Gauge Chart)
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = puan,
            title = {'text': "AI Görünürlük Skoru", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "darkblue"},
                'steps' : [
                    {'range': [0, 40], 'color': "#ff4b4b"},
                    {'range': [40, 75], 'color': "#ffa500"},
                    {'range': [75, 100], 'color': "#00cc96"}]}))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🤖 Yapay Zeka Strateji Özeti")
        st.success(yorum)
        
        # Metrik Kartları
        m1, m2 = st.columns(2)
        conn = sqlite3.connect('arsiv.db')
        toplam_icerik = pd.read_sql(f"SELECT COUNT(*) FROM icerikler WHERE marka='{marka_adi}'", conn).values[0][0]
        m1.metric("Toplam İçerik", toplam_icerik)
        m2.metric("Durum", "Yükseliyor 🚀")
        conn.close()

    st.divider()
    st.subheader("📈 Skor Gelişim Trendi")
    conn = sqlite3.connect('arsiv.db')
    df_trend = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    if not df_trend.empty:
        st.line_chart(df_trend.set_index('tarih'))
    conn.close()    # 3. Gelişim Grafiği
    st.subheader("📈 AI Görünürlük Trendi")
    conn = sqlite3.connect('arsiv.db')
    df_trend = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    if not df_trend.empty:
        st.line_chart(df_trend.set_index('tarih'))
    else:
        st.info("Veriler toplandıkça gelişim grafiği burada şekillenecek.")
    conn.close()
# --- 2. RAKİP TARAYICI ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Site Tarayıcı")
    r_url = st.text_input("Rakip URL")
    if st.button("Analiz Et"):
        st.info(f"{r_url} analiz ediliyor...")

import re # Metin parçalama için gerekli

# --- 3. İÇERİK ÜRETİMİ (TAM DOLU SEKMELER) ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik & Görsel Fabrikası")
    
    with st.container():
        c1, c2 = st.columns([2, 1])
        with c1:
            topic = st.text_input("📝 Ana Konu Başlığı", value="Restoranlar için sanal pos avantajları")
        with c2:
            target_tone = st.selectbox("🎭 İçerik Üslubu", ["Kurumsal", "Samimi", "Teknik"])
    
    st.divider()

    if st.button("🌟 Tüm İçerik Paketini Hazırla", use_container_width=True):
        if not topic:
            st.error("Lütfen bir konu başlığı girin!")
        else:
            with st.spinner("AI fabrikanız tüm sekmeleri dolduruyor..."):
                # AI'dan ayrıştırıcı etiketlerle içerik istiyoruz
                prompt = f"""
                Konu: {topic}
                Lütfen içeriği tam olarak şu etiketler arasına yaz:
                [BLOG_BASLA] ... [BLOG_BITIR]
                [SOSYAL_BASLA] ... [SOSYAL_BITIR]
                [BULTEN_BASLA] ... [BULTEN_BITIR]
                [VIDEO_BASLA] ... [VIDEO_BITIR]
                """
                
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                
                # METİN PARÇALAMA MANTIĞI (Regex)
                def extract_part(tag):
                    pattern = f"\[{tag}_BASLA\](.*?)\[{tag}_BITIR\]"
                    match = re.search(pattern, response, re.DOTALL)
                    return match.group(1).strip() if match else ""

                blog_content = extract_part("BLOG")
                sosyal_content = extract_part("SOSYAL")
                bulten_content = extract_part("BULTEN")
                video_content = extract_part("VIDEO")

                # SEKMELERİ OLUŞTUR VE DOLDUR
                tab1, tab2, tab3, tab4 = st.tabs(["📝 Blog & SEO", "📱 Sosyal Medya", "📧 E-Bülten", "🎬 Video/Reels"])
                
                with tab1:
                    st.markdown(blog_content if blog_content else response)
                    # Kayıt
                    icerik_kaydet(st.session_state["aktif_kullanici"], marka_adi, topic, blog_content, tip="Blog")

                with tab2:
                    st.subheader("📱 Sosyal Medya Kanalları")
                    if sosyal_content:
                        st.info("LinkedIn ve Instagram için hazır metinleriniz:")
                        st.markdown(sosyal_content)
                    else:
                        st.warning("Sosyal medya içeriği parçalanamadı. Lütfen tekrar deneyin.")

                with tab3:
                    st.subheader("📧 Haftalık Bülten Taslağı")
                    if bulten_content:
                        st.markdown(bulten_content)
                    else:
                        st.write("Bülten taslağı hazırlanıyor...")

                with tab4:
                    st.subheader("🎬 Kısa Video Senaryosu")
                    st.markdown(video_content if video_content else "Senaryo hazırlanıyor...")# --- 4. ARŞİV ---
elif nav == "📜 Arşiv":
    st.title("📜 İçerik Arşivi")
    conn = sqlite3.connect('arsiv.db')
    df_arsiv = pd.read_sql("SELECT tarih, konu, icerik FROM icerikler ORDER BY id DESC", conn)
    for i, row in df_arsiv.iterrows():
        with st.expander(f"{row['tarih']} | {row['konu']}"):
            st.markdown(row['icerik'])
    conn.close()