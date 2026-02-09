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
st.set_page_config(page_title="VetraPos AI Ultimate SaaS", layout="wide", page_icon="📈")

# --- VERİTABANI MİMARİSİ ---
def init_db():
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS icerikler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, marka TEXT, konu TEXT, icerik TEXT, tarih TEXT, tip TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS skorlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, marka TEXT, puan INTEGER, tarih TEXT)''')
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
    st.title("🔐 VetraPos AI Pro Giriş")
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

# --- PDF RAPORLAMA MODÜLÜ ---
def generate_weekly_pdf(marka, user):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 20, txt=f"{marka} Haftalik Performans Raporu", ln=1, align='C')
    
    conn = sqlite3.connect('arsiv.db')
    # Son 7 günün içerikleri
    df_recent = pd.read_sql(f"SELECT tarih, konu FROM icerikler WHERE marka='{marka}' ORDER BY id DESC LIMIT 5", conn)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Son Uretilen Icerikler:", ln=1)
    pdf.set_font("Arial", size=11)
    for i, row in df_recent.iterrows():
        pdf.cell(200, 8, txt=f"- {row['tarih']}: {row['konu']}", ln=1)
        
    # Skor gelişimi
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="AI Gorunurluk Ozeti:", ln=1)
    df_skor = pd.read_sql(f"SELECT puan FROM skorlar WHERE marka='{marka}' ORDER BY id DESC LIMIT 1", conn)
    puan = df_skor['puan'].values[0] if not df_skor.empty else "Veri Yok"
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, txt=f"Guncel AI Puaniniz: {puan}/100", ln=1)
    
    conn.close()
    return pdf.output(dest='S').encode('latin-1')

# --- ZEKA MODÜLLERİ ---
def get_rakip_analizi(rakip_url, kendi_markan):
    prompt = f"{rakip_url} adresindeki rakibi incele. {kendi_markan} markasının bu rakibi SEO'da geçmesi için yazması gereken 3 kritik başlık öner."
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    return res.choices[0].message.content

def get_canli_skor(marka, sektor):
    prompt = f"{marka} markasının {sektor} sektöründeki yapay zeka bilinirlik puanını (0-100) sadece rakam olarak ver."
    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
    try:
        puan = int(''.join(filter(str.isdigit, res.choices[0].message.content)))
        skor_kaydet(marka, puan)
        return puan
    except: return 45

# --- ARAYÜZ ---
with st.sidebar:
    st.title(f"Hoş geldin, {st.session_state['aktif_kullanici']}")
    marka_adi = st.text_input("Ana Marka", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    rakip_url_input = st.text_input("Rakip URL")
    
    st.divider()
    nav = st.radio("Navigasyon", ["📊 Dashboard", "🕵️ Rakip Analizi", "✍️ İçerik Üretimi", "📅 Yayın Takvimi", "📜 Arşiv", "📧 Raporlama"])
    
    if st.button("Çıkış"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

# --- DASHBOARD ---
if nav == "📊 Dashboard":
    st.title("📊 Stratejik Performans Paneli")
    c1, c2, c3 = st.columns(3)
    p = get_canli_skor(marka_adi, sektor_adi)
    c1.metric("AI Bilinirlik Skoru", f"{p}/100", delta="+3%")
    conn = sqlite3.connect('arsiv.db')
    toplam = pd.read_sql(f"SELECT COUNT(*) FROM icerikler WHERE marka='{marka_adi}'", conn).values[0][0]
    c2.metric("Toplam İçerik", toplam)
    c3.metric("Durum", "Aktif")
    
    df_skor = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}'", conn)
    if not df_skor.empty: st.line_chart(df_skor.set_index('tarih'))
    conn.close()

# --- RAKİP ANALİZİ ---
elif nav == "🕵️ Rakip Analizi":
    st.title("🕵️ Rakip Analiz Modülü")
    if st.button("Analizi Başlat"):
        if rakip_url_input:
            with st.spinner("Taranıyor..."):
                st.markdown(get_rakip_analizi(rakip_url_input, marka_adi))
        else: st.warning("URL girin.")

# --- İÇERİK ÜRETİMİ ---
elif nav == "✍️ İçerik Üretimi":
    st.title("✍️ İçerik Fabrikası")
    konu_input = st.text_input("Konu?")
    if st.button("Üret ve Kaydet"):
        with st.spinner("Yazılıyor..."):
            prompt = f"{konu_input} konusunda {marka_adi} için içerik paketi üret."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
            st.markdown(res)
            icerik_kaydet(st.session_state["aktif_kullanici"], marka_adi, konu_input, res)

# --- YAYIN TAKVİMİ ---
elif nav == "📅 Yayın Takvimi":
    st.title("📅 Yayın Planlayıcı")
    p_konu = st.text_input("Konu")
    p_tarih = st.date_input("Tarih")
    if st.button("Kaydet"):
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("INSERT INTO planlar (marka, konu, durum, plan_tarihi) VALUES (?, ?, 'Planlandi', ?)", (marka_adi, p_konu, str(p_tarih)))
        conn.commit()
        conn.close()
    conn = sqlite3.connect('arsiv.db')
    st.table(pd.read_sql(f"SELECT plan_tarihi, konu FROM planlar WHERE marka='{marka_adi}'", conn))
    conn.close()

# --- ARŞİV ---
elif nav == "📜 Arşiv":
    st.title("📜 İçerik Kütüphanesi")
    conn = sqlite3.connect('arsiv.db')
    df = pd.read_sql(f"SELECT tarih, konu, icerik FROM icerikler WHERE marka='{marka_adi}' ORDER BY id DESC", conn)
    for i, row in df.iterrows():
        with st.expander(f"{row['tarih']} | {row['konu']}"): st.markdown(row['icerik'])
    conn.close()

# --- RAPORLAMA MODÜLÜ (YENİ) ---
elif nav == "📧 Raporlama":
    st.title("📧 Haftalık Yönetici Raporu")
    st.info("Bu modül, markanızın haftalık performansını özetleyen profesyonel bir PDF raporu oluşturur.")
    
    email_alici = st.text_input("Raporun Gönderileceği E-posta", "musteri@sirket.com")
    
    if st.button("📊 Haftalık Raporu Hazırla"):
        with st.spinner("Veriler derleniyor ve PDF oluşturuluyor..."):
            pdf_data = generate_weekly_pdf(marka_adi, st.session_state['aktif_kullanici'])
            st.success("✅ Haftalık raporunuz başarıyla oluşturuldu!")
            st.download_button(label="📄 PDF Raporu İndir", data=pdf_data, file_name=f"{marka_adi}_Haftalik_Rapor.pdf", mime="application/pdf")
            st.info(f"📧 Rapor simülasyon olarak {email_alici} adresine kuyruğa alındı.")