import streamlit as st
from openai import OpenAI
import time
import requests
import base64
from fpdf import FPDF
import sqlite3

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Agency Pro", layout="wide")

# --- VERITABANI HAZIRLIGI ---
def init_db():
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS icerikler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  kullanici TEXT, marka TEXT, konu TEXT, icerik TEXT, tarih TEXT)''')
    conn.commit()
    conn.close()

init_db()

def icerik_kaydet(kullanici, marka, konu, icerik):
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    tarih = time.strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO icerikler (kullanici, marka, konu, icerik, tarih) VALUES (?, ?, ?, ?, ?)",
              (kullanici, marka, konu, icerik, tarih))
    conn.commit()
    conn.close()

# --- PROFESYONEL GIRIS SISTEMI ---
KULLANICILAR = {"admin": "12345", "ahmet_bey": "ahmet123", "demo": "demo1"}

if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False
    st.session_state["aktif_kullanici"] = ""

def giris_ekrani():
    st.title("🔐 Güvenli Giriş Paneli")
    kullanici_adi = st.text_input("Kullanıcı Adı")
    sifre = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if kullanici_adi in KULLANICILAR and KULLANICILAR[kullanici_adi] == sifre:
            st.session_state["giris_yapildi"] = True
            st.session_state["aktif_kullanici"] = kullanici_adi
            st.rerun()
        else:
            st.error("Hatalı giriş!")
    st.stop()

if not st.session_state["giris_yapildi"]:
    giris_ekrani()

# 1. API ANAHTARI
api_key = "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" 

try:
    client = OpenAI(api_key=api_key)
except:
    st.error("API Key hatası!")
    st.stop()

# --- FONKSIYONLAR ---
def clean_text_for_pdf(text):
    replacements = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."}
    for k, v in replacements.items(): text = text.replace(k, v)
    tr_map = {"ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ç": "c", "Ç": "C", "ü": "u", "Ü": "U"}
    for k, v in tr_map.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf_report(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="VetraPos AI SEO Raporu", ln=1, align='C')
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt=clean_text_for_pdf(content))
    return pdf.output(dest='S').encode('latin-1')

def post_to_wordpress(title, content, wp_url, wp_user, wp_pass):
    creds = f"{wp_user}:{wp_pass}"
    token = base64.b64encode(creds.encode()).decode("utf-8")
    headers = {'Authorization': f'Basic {token}'}
    post = {'title': title, 'content': content, 'status': 'draft'}
    r = requests.post(f"{wp_url}/wp-json/wp/v2/posts", headers=headers, json=post)
    return "✅ Gönderildi" if r.status_code == 201 else f"❌ Hata: {r.status_code}"

# --- AI MODULLERI ---
def get_ai_suggestions(brand, sector):
    p = f"{brand} ({sector}) için SEO analizi ve 5 konu önerisi ver."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p}]).choices[0].message.content

def get_ai_brand_awareness(brand, sector):
    p = f"{brand} ({sector}) markasinin AI karnesini cikar, puan ver ve 3 makale konusu oner."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p}]).choices[0].message.content

def get_content_calendar(brand, sector):
    p = f"{brand} ({sector}) için 1 aylik tablo formatinda icerik takvimi hazirla."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p}]).choices[0].message.content

def write_full_article(topic, brand, tone):
    p = f"{topic} konusunda {brand} icin {tone} dilde 600 kelimelik SEO blogu yaz."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p}]).choices[0].message.content

def generate_image(topic):
    return client.images.generate(model="dall-e-3", prompt=f"Professional photo for: {topic}", n=1).data[0].url

# --- ARAYÜZ ---
with st.sidebar:
    st.header(f"👤 {st.session_state['aktif_kullanici']}")
    if st.button("Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.rerun()
    st.divider()
    marka_adi = st.text_input("Marka Adı")
    sektor = st.text_input("Sektör")
    uslup = st.selectbox("Üslup", ["Kurumsal", "Samimi", "Teknik"])
    
    st.divider()
    if st.button("📜 Arşivi Görüntüle"):
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("SELECT tarih, marka, konu, icerik FROM icerikler WHERE kullanici=? ORDER BY id DESC", (st.session_state["aktif_kullanici"],))
        rows = c.fetchall()
        conn.close()
        for row in rows:
            with st.expander(f"📅 {row[0]} | {row[1]}"):
                st.write(f"**Konu:** {row[2]}")
                st.markdown(row[3])

st.title("🚀 VetraPos AI Agency Pro")
col1, col2 = st.columns(2)

with col1:
    st.info("🕵️ Analiz Merkezi")
    if st.button("🚀 Genel Analiz"):
        res = get_ai_suggestions(marka_adi, sektor)
        st.markdown(res)
        st.download_button("📄 PDF İndir", create_pdf_report(res), "rapor.pdf")
    if st.button("🤖 AI Marka Karnesi"):
        st.write(get_ai_brand_awareness(marka_adi, sektor))
    if st.button("📅 1 Aylık Takvim"):
        st.write(get_content_calendar(marka_adi, sektor))

with col2:
    st.success("✍️ Üretim Merkezi")
    topic = st.text_area("Konu:")
    gen_img = st.checkbox("📸 Görsel Üret (DALL-E 3)")
    
    if st.button("📝 Makale Yaz"):
        art = write_full_article(topic, marka_adi, uslup)
        st.markdown(art)
        # VERITABANINA KAYDET
        icerik_kaydet(st.session_state["aktif_kullanici"], marka_adi, topic, art)
        st.success("✅ Arşive Kaydedildi!")
        
        if gen_img:
            st.image(generate_image(topic))