import streamlit as st
from openai import OpenAI
import time
import sqlite3
import requests
import base64
from fpdf import FPDF

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Agency Pro", layout="wide")

# --- PROFESYONEL GIRIS SISTEMI ---
KULLANICILAR = {
    "admin": "12345",
    "ahmet_bey": "ahmet123",
    "demo": "demo1"
}

if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False
    st.session_state["aktif_kullanici"] = ""

def giris_ekrani():
    st.markdown("""<style>.stTextInput > label {font-size:105%; font-weight:bold; color:blue;}</style>""", unsafe_allow_html=True)
    st.title("🔐 Güvenli Giriş Paneli")
    st.info("Lütfen size verilen kullanıcı adı ve şifre ile giriş yapın.")
    
    kullanici_adi = st.text_input("Kullanıcı Adı")
    sifre = st.text_input("Şifre", type="password")
    
    if st.button("Giriş Yap"):
        if kullanici_adi in KULLANICILAR and KULLANICILAR[kullanici_adi] == sifre:
            st.session_state["giris_yapildi"] = True
            st.session_state["aktif_kullanici"] = kullanici_adi
            st.success(f"Hoşgeldiniz Sayın {kullanici_adi}! Panel Yükleniyor...")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    st.stop()

if not st.session_state["giris_yapildi"]:
    giris_ekrani()

# --- ANA UYGULAMA BASLANGICI ---

# 1. API ANAHTARI
api_key = "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" 

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

try:
    client = OpenAI(api_key=api_key)
except:
    st.error("API Key hatası! Lütfen kodun 37. satırına şifrenizi doğru yapıştırdığınızdan emin olun.")
    st.stop()

# --- YARDIMCI FONKSIYONLAR (PDF VE WP) ---

def clean_text_for_pdf(text):
    # --- PDF HATALARINI ONLEYEN TEMIZLIK ROBOTU ---
    # 1. GPT'nin kullandığı süslü/kıvrık tırnakları düzeltiyoruz (Bu kısım hatayı çözer)
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "…": "..."
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # 2. Türkçe karakterleri PDF'in anlayacağı "Güvenli Latin" formatına zorluyoruz.
    # FPDF standart fontu Türkçe karakterleri (ğ, ş, ı) desteklemez ve bozuk çıkarır.
    # O yüzden bunları en yakın harfe (g, s, i) çeviriyoruz ki PDF ÇÖKMESİN.
    tr_map = {
        "ğ": "g", "Ğ": "G", "ş": "s", "Ş": "S", "ı": "i", "İ": "I",
        "ö": "o", "Ö": "O", "ç": "c", "Ç": "C", "ü": "u", "Ü": "U"
    }
    for k, v in tr_map.items():
        text = text.replace(k, v)
    
    # 3. Son güvenlik önlemi: Tanınmayan her şeyi sil (Latin-1'e zorla)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf_report(content, filename="rapor.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Baslik
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="VetraPos AI SEO Raporu", ln=1, align='C')
    
    # Icerik (Temizlenmis metin ile)
    pdf.set_font("Arial", size=10)
    clean_content = clean_text_for_pdf(content)
    pdf.multi_cell(0, 10, txt=clean_content)
    
    return pdf.output(dest='S').encode('latin-1')

def post_to_wordpress(title, content, wp_url, wp_user, wp_password):
    # WordPress REST API Entegrasyonu
    creds = f"{wp_user}:{wp_password}"
    token = base64.b64encode(creds.encode())
    headers = {'Authorization': f'Basic {token.decode("utf-8")}'}
    
    post = {
        'title': title,
        'content': content,
        'status': 'draft' # Güvenlik için taslak olarak atar
    }
    
    try:
        r = requests.post(f"{wp_url}/wp-json/wp/v2/posts", headers=headers, json=post)
        if r.status_code == 201:
            return f"✅ Başarılı! Yazı ID: {r.json()['id']} olarak taslaklara eklendi."
        else:
            return f"❌ Hata: {r.status_code} - {r.text}"
    except Exception as e:
        return f"Bağlantı Hatası: {e}"

# 2. YAN MENU (SIDEBAR)
with st.sidebar:
    st.success(f"👤 {st.session_state['aktif_kullanici']}")
    if st.button("Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.rerun()
    
    st.divider()
    st.header("⚙️ Marka Ayarları")
    marka_adi = st.text_input("Marka Adı", value="")
    sektor = st.text_input("Sektör", value="")
    uslup = st.selectbox("Marka Dili", ["Kurumsal", "Samimi", "Teknik", "Satış Odaklı"])
    
    st.divider()
    st.header("🌐 WordPress Ayarları")
    st.info("Yazıları otomatik sitenize göndermek için doldurun (İsteğe bağlı).")
    wp_url = st.text_input("Site Adresi (örn: https://vetrapos.com)")
    wp_user = st.text_input("WP Kullanıcı Adı")
    wp_pass = st.text_input("WP Uygulama Şifresi", type="password", help="WP Admin > Kullanıcılar > Profil > Uygulama Şifreleri kısmından almalısınız.")

st.divider()
    if st.button("📜 Arşivi Görüntüle"):
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("SELECT tarih, marka, konu, icerik FROM icerikler WHERE kullanici=? ORDER BY id DESC", 
                  (st.session_state["aktif_kullanici"],))
        rows = c.fetchall()
        conn.close()
        
        if rows:
            for row in rows:
                with st.expander(f"📅 {row[0]} | {row[1]} - {row[2]}"):
                    st.markdown(row[3])
        else:
            st.info("Henüz kaydedilmiş bir içerik yok.")

# 3. YAPAY ZEKA FONKSIYONLARI

def get_ai_suggestions(brand, sector):
    prompt = f"Sen {brand} için {sector} sektöründe SEO uzmanısın. 5 blog konusu, 10 anahtar kelime, 3 rakip stratejisi öner. Markdown formatında yaz."
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

def get_ai_brand_awareness(brand, sector):
    prompt = f"Yapay zeka denetçisisin. {brand} ({sector}) için marka bilinirlik puanı (0-100), yapay zeka görüşü ve puanı artıracak 3 makale başlığı öner."
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

def get_content_calendar(brand, sector):
    prompt = f"{brand} ({sector}) için 4 haftalık içerik takvimi (Tablo formatında: Hafta, Konu, Kanal). Markdown tablosu ver."
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

def write_full_article(topic, brand, tone):
    prompt = f"Konu: {topic}. Marka: {brand}. Üslup: {tone}. 600 kelime, SEO uyumlu, HTML tablolu, Schema kodlu makale yaz."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Profesyonel yazar."}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

def generate_image(topic):
    # DALL-E 3 Görsel Üretimi
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"High quality, realistic, professional photo about: {topic}. Clean composition, suitable for a corporate blog header.",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        return None

def write_social_media_posts(topic, brand, tone):
    prompt = f"Konu: {topic}. Marka: {brand}. Üslup: {tone}. LinkedIn, Instagram, Twitter için post metinleri yaz."
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

def write_newsletter(topic, brand, tone):
    prompt = f"Konu: {topic}. Marka: {brand}. Üslup: {tone}. E-Bülten formatına çevir (Konu, Giriş, Gelişme, CTA)."
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

def generate_seo_tags(topic, brand):
    prompt = f"Konu: {topic}. Marka: {brand}. Title, Description, Slug, Alt Text, Keyword hazırla."
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

def generate_video_script(topic, brand, tone):
    prompt = f"Konu: {topic}. Marka: {brand}. Üslup: {tone}. 60sn Reels/TikTok senaryosu (Tablo formatında)."
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Hata: {e}"

# 4. ARAYÜZ TASARIMI
st.title("🚀 VetraPos AI Agency Pro")

col1, col2 = st.columns([1,1])

with col1:
    st.info("🕵️ **Analiz Merkezi**")
    
    c1, c2 = st.columns([1,1])
    if c1.button("🚀 Genel Analiz"):
        if marka_adi and sektor:
            with st.spinner("Analiz..."):
                res = get_ai_suggestions(marka_adi, sektor)
                st.markdown(res)
                # PDF İndirme Butonu (HATA BURADA DUZELTILDI)
                pdf_bytes = create_pdf_report(res)
                st.download_button("📄 PDF Raporu İndir", pdf_bytes, "analiz_raporu.pdf", "application/pdf")
        else: st.warning("Marka girin.")

    if c2.button("🤖 Marka Karnesi"):
        if marka_adi and sektor:
            with st.spinner("İnceleniyor..."):
                res = get_ai_brand_awareness(marka_adi, sektor)
                st.info("Marka Raporu")
                st.write(res)
        else: st.warning("Marka girin.")

    st.markdown("---")
    if st.button("📅 1 Aylık Takvim"):
        if marka_adi and sektor:
            with st.spinner("Planlanıyor..."):
                st.write(get_content_calendar(marka_adi, sektor))
        else: st.warning("Marka girin.")

with col2:
    st.success("✍️ **Üretim Merkezi**")
    topic = st.text_area("Konu Başlığı:", placeholder="Buraya bir başlık yapıştırın...")
    
    # Görsel Üretim Kutusu
    if st.checkbox("📸 Makale için Yapay Zeka Görseli de Üret (DALL-E 3)"):
        generate_img = True
    else:
        generate_img = False

    b1, b2 = st.columns([1,1])
    if b1.button("📝 Makale Yaz"):
        if len(topic) > 3:
            with st.spinner("Makale yazılıyor..."):
                art = write_full_article(topic, marka_adi, uslup)
                st.markdown(art)
                st.download_button("💾 İndir (MD)", art, "makale.md")
                # ... makale üretildikten sonra ...
st.markdown(art)
icerik_kaydet(st.session_state["aktif_kullanici"], marka_adi, topic, art) # BU SATIRI EKLE
st.success("✅ Makale veritabanına kaydedildi!")
                # Görsel Üretimi
                if generate_img:
                    with st.spinner("Görsel çiziliyor..."):
                        img_url = generate_image(topic)
                        if img_url:
                            st.image(img_url, caption="Yapay Zeka Tarafından Üretildi")
                            st.success("Görsel Başarıyla Üretildi!")
                        else:
                            st.error("Görsel üretilirken hata oluştu.")
                
                # WordPress'e Gönder Butonu (Eğer yazı yazıldıysa çıkar)
                if wp_url and wp_user and wp_pass:
                    if st.button("🌐 WordPress'e Taslak Olarak Gönder"):
                        with st.spinner("Siteye bağlanılıyor..."):
                            sonuc = post_to_wordpress(topic, art, wp_url, wp_user, wp_pass)
                            st.info(sonuc)
        else: st.warning("Konu girin.")

    if b2.button("🏷️ SEO Künyesi"):
        if len(topic) > 3:
            with st.spinner("Etiketler..."):
                st.write(generate_seo_tags(topic, marka_adi))

    st.markdown("---")
    b3, b4, b5 = st.columns([1,1,1])
    
    if b3.button("📱 Sosyal"):
        if len(topic) > 3:
            with st.spinner("Postlar..."):
                st.write(write_social_media_posts(topic, marka_adi, uslup))

    if b4.button("📧 E-Bülten"):
        if len(topic) > 3:
            with st.spinner("Mail..."):
                st.write(write_newsletter(topic, marka_adi, uslup))

    if b5.button("🎬 Video"):
        if len(topic) > 3:
            with st.spinner("Senaryo..."):
                st.write(generate_video_script(topic, marka_adi, uslup))