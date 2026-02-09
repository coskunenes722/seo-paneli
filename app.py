import streamlit as st
from openai import OpenAI
import time
import requests
import base64
from fpdf import FPDF
import sqlite3
import pandas as pd
import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate SaaS", layout="wide", page_icon="🏆")

# --- VERİTABANI MİMARİSİ ---
def init_db():
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    # İçerikler
    c.execute('''CREATE TABLE IF NOT EXISTS icerikler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, marka TEXT, konu TEXT, icerik TEXT, tarih TEXT, tip TEXT)''')
    # Canlı Skor (Grafik İçin)
    c.execute('''CREATE TABLE IF NOT EXISTS skorlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, marka TEXT, puan INTEGER, tarih TEXT)''')
    # Gelişmiş Takvim
    c.execute('''CREATE TABLE IF NOT EXISTS planlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, marka TEXT, konu TEXT, durum TEXT, plan_tarihi TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- VERİ İŞLEME FONKSİYONLARI ---
def icerik_kaydet(kullanici, marka, konu, icerik, tip="Makale"):
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    tarih = time.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO icerikler (kullanici, marka, konu, icerik, tarih, tip) VALUES (?, ?, ?, ?, ?, ?)",
              (kullanici, marka, konu, icerik, tarih, tip))
    conn.commit()
    conn.close()

def skor_kaydet(marka, puan):
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    tarih = time.strftime('%Y-%m-%d')
    c.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka, puan, tarih))
    conn.commit()
    conn.close()

# --- GİRİŞ KONTROLÜ ---
KULLANICILAR = {"admin": "12345", "ahmet_bey": "ahmet123"}
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False

if not st.session_state["giris_yapildi"]:
    st.title("🔐 VetraPos AI Ultimate Giriş")
    k = st.text_input("Kullanıcı Adı")
    s = st.text_input("Şifre", type="password")
    if st.button("Sisteme Giriş Yap"):
        if k in KULLANICILAR and KULLANICILAR[k] == s:
            st.session_state["giris_yapildi"] = True
            st.session_state["aktif_kullanici"] = k
            st.rerun()
    st.stop()

# --- API YAPILANDIRMASI ---
api_key = "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" 
client = OpenAI(api_key=api_key)

# --- ZEKA MODÜLLERİ ---

def get_rakip_analizi(rakip_url, kendi_markan):
    # Rakip Site Tarayıcı Modülü
    prompt = f"Şu rakip URL'sini ({rakip_url}) analiz et. {kendi_markan} markasının bu rakibi geçmesi için yazması gereken, rakibin sitesinde olmayan 3 kritik stratejik başlık ve içerik planı öner."
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    return res.choices[0].message.content

def get_canli_skor(marka, sektor):
    # Canlı Skor Panosu Modülü
    prompt = f"{marka} markasının {sektor} sektöründeki AI bilinirlik ve görünürlük puanını (0-100) sadece rakam olarak ver."
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    try:
        puan = int(''.join(filter(str.isdigit, res.choices[0].message.content)))
        skor_kaydet(marka, puan)
        return puan
    except: return 50

# --- ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title(f"👋 {st.session_state['aktif_kullanici']}")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    rakip_url_input = st.text_input("Rakip Site URL")
    
    st.divider()
    nav = st.radio("Sistem Menüsü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Fabrikası", "📅 Otomatik Planlayıcı", "📜 Arşiv", "📧 Raporlama"])
    
    if st.button("Güvenli Çıkış"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

# --- 1. DASHBOARD (CANLI SKOR PANOSU) ---
if nav == "📊 Dashboard":
    st.title("📊 Marka Görünürlük Dashboard")
    
    # Metrikler
    puan = get_canli_skor(marka_adi, sektor_adi)
    c1, c2, c3 = st.columns(3)
    c1.metric("Güncel AI Skoru", f"{puan}/100", delta="+2%")
    
    conn = sqlite3.connect('arsiv.db')
    toplam = pd.read_sql(f"SELECT COUNT(*) FROM icerikler WHERE marka='{marka_adi}'", conn).values[0][0]
    c2.metric("Üretilen İçerikler", toplam)
    c3.metric("Pazar Konumu", "Yükseliyor")

    # ETKİLEŞİMLİ GRAFİK (Canlı Skor Takibi)
    st.subheader("📈 Gün Bazında AI Görünürlük Takibi")
    df_skor = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    if not df_skor.empty:
        st.line_chart(df_skor.set_index('tarih'))
    else:
        st.info("Henüz veri birikmedi. İlk analizi yaptığınızda grafik oluşacak.")
    conn.close()

# --- 2. RAKİP TARAYICI ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Site Tarayıcı & Analiz")
    if st.button("Rakibi Derinlemesine Analiz Et"):
        if rakip_url_input:
            with st.spinner("Rakip verileri taranıyor..."):
                analiz = get_rakip_analizi(rakip_url_input, marka_adi)
                st.markdown(analiz)
        else: st.warning("Analiz için bir rakip URL girin.")

# --- 3. İÇERİK FABRİKASI ---
elif nav == "✍️ İçerik Fabrikası":
    st.title("✍️ Çok Kanallı İçerik Üretimi")
    topic = st.text_input("Konu nedir?")
    if st.button("Paketi Üret (Makale + Sosyal Medya + Bülten)"):
        with st.spinner("AI Fabrikası çalışıyor..."):
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": f"{topic} konusunda {marka_adi} için içerik paketi üret."}]).choices[0].message.content
            st.markdown(res)
            icerik_kaydet(st.session_state["aktif_kullanici"], marka_adi, topic, res)
            st.success("Tüm içerikler arşive kaydedildi!")

# --- 4. OTOMATİK PLANLAYICI ---
elif nav == "📅 Otomatik Planlayıcı":
    st.title("📅 İçerik Yayın Planlayıcı (Scheduler)")
    p_konu = st.text_input("Planlanacak İçerik Konusu")
    p_tarih = st.date_input("Planlanan Yayın Tarihi")
    if st.button("Takvime Ekle"):
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("INSERT INTO planlar (marka, konu, durum, plan_tarihi) VALUES (?, ?, 'Bekliyor', ?)", (marka_adi, p_konu, str(p_tarih)))
        conn.commit()
        conn.close()
        st.success("İçerik başarıyla takvime eklendi!")

    st.divider()
    st.subheader("🗓️ Yayın Akışı")
    conn = sqlite3.connect('arsiv.db')
    df_plan = pd.read_sql(f"SELECT plan_tarihi as 'Tarih', konu as 'Konu', durum as 'Durum' FROM planlar WHERE marka='{marka_adi}' ORDER BY plan_tarihi ASC", conn)
    st.table(df_plan)
    conn.close()

# --- 5. ARŞİV ---
elif nav == "📜 Arşiv":
    st.title("📜 Marka İçerik Kütüphanesi")
    conn = sqlite3.connect('arsiv.db')
    df_arsiv = pd.read_sql(f"SELECT tarih, konu, icerik FROM icerikler WHERE kullanici='{st.session_state['aktif_kullanici']}' ORDER BY id DESC", conn)
    for i, row in df_arsiv.iterrows():
        with st.expander(f"📅 {row['tarih']} | {row['konu']}"):
            st.markdown(row['icerik'])
    conn.close()

# --- 6. RAPORLAMA ---
elif nav == "📧 Raporlama":
    st.title("📧 Yönetici Özeti & PDF Rapor")
    st.info("Haftalık performans raporunuzu buradan indirebilirsiniz.")
    # (Önceki raporlama fonksiyonu kullanılabilir)