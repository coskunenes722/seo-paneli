import streamlit as st
from openai import OpenAI
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Agency", layout="wide")

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

# 1. API ANAHTARI (BURAYA KENDİ ŞİFRENİ YAPIŞTIR)
api_key = "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" 

try:
    client = OpenAI(api_key=api_key)
except:
    st.error("API Key hatası! Lütfen kodun 37. satırına şifrenizi doğru yapıştırdığınızdan emin olun.")
    st.stop()

# 2. YAN MENU (SIDEBAR)
with st.sidebar:
    st.success(f"👤 Giriş Yapan: {st.session_state['aktif_kullanici']}")
    if st.button("Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.rerun()
    
    st.divider()
    st.header("⚙️ Ayarlar")
    marka_adi = st.text_input("Marka Adı", value="")
    sektor = st.text_input("Sektör", value="")
    
    # Üslup Seçimi
    uslup = st.selectbox(
        "Marka Dili (Üslup)", 
        ["Kurumsal ve Profesyonel", "Samimi ve Eğlenceli", "Bilimsel ve Teknik", "İkna Edici ve Satış Odaklı"]
    )
    
    st.info("Marka ve Sektör girmezseniz analiz çalışmaz.")

# 3. YAPAY ZEKA FONKSIYONLARI (TÜMÜ)

def get_ai_suggestions(brand, sector):
    # Analiz
    prompt = f"""
    Sen {brand} markası için {sector} sektöründe uzman bir SEO stratejistisin.
    Lütfen şu 3 başlık altında detaylı bir analiz yap:
    1. **5 Adet Teknik Blog Konusu:** {brand} markasının otoritesini artıracak, az bilinen ama çok aranan 5 teknik konu öner.
    2. **Anahtar Kelime Analizi:** {sector} sektörü için hacmi yüksek ama rekabeti düşük 10 adet "Long-tail" (uzun kuyruklu) anahtar kelime öner.
    3. **Rakip Analizi:** {sector} sektöründeki rakiplerin genellikle neleri eksik yaptığını ve {brand} markasının nasıl öne çıkabileceğini anlatan 3 maddelik strateji ver.
    Lütfen çıktılarını şık bir formatta, başlıklarla ayırarak ver.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def get_ai_brand_awareness(brand, sector):
    # Marka Karnesi
    prompt = f"""
    Sen bir Yapay Zeka Denetçisisin. "{brand}" markasını {sector} sektöründe analiz et.
    Bana şu formatta samimi bir rapor ver:
    1. **Bilinirlik Skoru:** (0 ile 100 arasında bir puan ver. Marka çok yeniyse düşük ver.)
    2. **Yapay Zeka Görüşü:** (ChatGPT olarak bu marka hakkında ne biliyorsun? Olumlu/Olumsuz/Nötr mü?)
    3. **Eksik Gedik:** (Genel olarak neler eksik?)
    4. **🚀 Puanı Yükseltecek 3 Altın Makale Konusu:** (Markanın bilinirliğini artırmak için hemen yazılması gereken, dikkat çekici 3 tam makale başlığı öner.)
    Lütfen çıktılarını şık bir formatta, başlıklarla ayırarak ver.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def get_content_calendar(brand, sector):
    # YENI: 1 Aylık İçerik Takvimi
    prompt = f"""
    Marka: {brand}. Sektör: {sector}.
    
    Bu marka için 4 haftalık (1 aylık) stratejik bir içerik takvimi hazırla.
    Çıktıyı Markdown TABLOSU olarak ver.
    
    Tablo Sütunları: [Hafta, Odak Konusu, Blog Başlığı, Sosyal Medya Fikri (Reels/Post)]
    
    Her hafta için farklı bir strateji (Örn: Bilinirlik, Satış, Güven, Eğitim) belirle.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def write_full_article(topic, brand, tone):
    # Makale Yazari
    prompt = f"""
    Konu: {topic}. Marka: {brand}. 
    Dil ve Üslup: {tone} bir dille yazılacak.
    
    600 kelimelik, SEO uyumlu, teknik bir blog yazısı yaz.
    - İçinde mutlaka bir HTML tablosu olsun.
    - Alt başlıklar (h2, h3) kullan.
    - İçeriğin en altına JSON-LD formatında Schema (FAQ) kodu ekle.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Sen {brand} markası için {tone} içerik üreten profesyonel bir yazarsın."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def write_social_media_posts(topic, brand, tone):
    # Sosyal Medya
    prompt = f"""
    Konu: "{topic}". Marka: {brand}. Üslup: {tone}.
    Bu blog yazısını tanıtmak için 3 farklı platforma içerik hazırla:
    1. **LinkedIn Gönderisi:** (Profesyonel, emojili, hashtag'li)
    2. **Instagram Açıklaması:** (Samimi, harekete geçirici, bol hashtag'li)
    3. **Twitter (X) Flood:** (3 tweetlik kısa, vurucu bir seri)
    Hepsini başlıklarla ayır.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def write_newsletter(topic, brand, tone):
    # E-Bülten
    prompt = f"""
    Konu: "{topic}". Marka: {brand}. Üslup: {tone}.
    Bu blog yazısını, mevcut müşterilere gönderilecek profesyonel bir E-Bülten formatına çevir.
    Format: Konu Satırı, Selamlama, Giriş (Sorun), Gelişme (Çözüm), CTA (Tıklama Çağrısı).
    Mobil uyumlu, kısa paragraflar kullan.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def generate_seo_tags(topic, brand):
    # SEO Künyesi
    prompt = f"""
    Konu: "{topic}". Marka: {brand}.
    Bu blog yazısı için Google'ın seveceği teknik SEO etiketlerini hazırla.
    Format:
    1. **SEO Başlığı (Title):** (Max 60 karakter).
    2. **Meta Açıklaması (Description):** (Max 160 karakter).
    3. **SEO Dostu URL (Slug):** (kisa-tireli-yapida).
    4. **Görsel Alt Etiketi:** (Anahtar kelimeli).
    5. **Odak Anahtar Kelime:**
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def generate_video_script(topic, brand, tone):
    # YENI: Video Senaryosu
    prompt = f"""
    Konu: "{topic}". Marka: {brand}. Üslup: {tone}.
    
    Bu konu hakkında Instagram Reels / TikTok / YouTube Shorts için 60 saniyelik virallik potansiyeli yüksek bir senaryo yaz.
    
    Tablo Formatında Olsun:
    [Süre, Görsel Sahne, Seslendirme (Dış Ses/Konuşma), Ekrana Gelecek Yazı]
    
    0-5sn: Çok güçlü bir kanca (Hook) ile başla.
    Sonunda mutlaka harekete geçirici mesaj (CTA) olsun.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

# 4. ANA SAYFA TASARIMI
st.title("🚀 Yapay Zeka SEO & Sosyal Medya Paneli")

col1, col2 = st.columns([1,1])

with col1:
    st.info("🕵️ **1. Adım: Analiz & Strateji**")
    
    # Analiz Butonlari
    c1, c2 = st.columns([1,1])
    
    if c1.button("🚀 Genel Analiz"):
        if not marka_adi or not sektor:
            st.error("Marka ve Sektör girin!")
        else:
            with st.spinner("Analiz yapılıyor..."):
                sonuc = get_ai_suggestions(marka_adi, sektor)
                st.markdown(sonuc)

    if c2.button("🤖 Marka Karnesi"):
        if not marka_adi or not sektor:
            st.error("Marka ve Sektör girin!")
        else:
            with st.spinner("Marka inceleniyor..."):
                karne = get_ai_brand_awareness(marka_adi, sektor)
                st.info("### 📢 Marka Bilinirlik Raporu")
                st.write(karne)

    st.markdown("---")
    
    # YENI: Icerik Takvimi Butonu
    if st.button("📅 1 Aylık İçerik Takvimi Oluştur"):
        if not marka_adi or not sektor:
            st.error("Lütfen marka ve sektör girin!")
        else:
            with st.spinner("Stratejik plan hazırlanıyor..."):
                takvim = get_content_calendar(marka_adi, sektor)
                st.success("### 🗓️ 30 Günlük Yol Haritası")
                st.write(takvim)

with col2:
    st.success("✍️ **2. Adım: İçerik Üretimi**")
    topic_input = st.text_area("Hangi konuyu yazalım?", placeholder="Bir başlık yapıştırın...")
    
    # 1. Satir Butonlar
    b1, b2 = st.columns([1,1])
    if b1.button("📝 Makaleyi Yaz"):
        if len(topic_input) > 3:
            with st.spinner("Yazılıyor..."):
                art = write_full_article(topic_input, marka_adi, uslup)
                st.markdown(art)
                st.download_button("💾 İndir", art, file_name="makale.md")
        else: st.warning("Konu giriniz.")

    if b2.button("🏷️ SEO Künyesi"):
        if len(topic_input) > 3:
            with st.spinner("Etiketler..."):
                tags = generate_seo_tags(topic_input, marka_adi)
                st.write(tags)
        else: st.warning("Konu giriniz.")

    st.markdown("---") # Ayirac

    # 2. Satir Butonlar
    b3, b4, b5 = st.columns([1,1,1])
    
    if b3.button("📱 Sosyal Medya"):
        if len(topic_input) > 3:
            with st.spinner("Postlar..."):
                st.write(write_social_media_posts(topic_input, marka_adi, uslup))
        else: st.warning("Konu giriniz.")

    if b4.button("📧 E-Bülten"):
        if len(topic_input) > 3:
            with st.spinner("Mail..."):
                st.write(write_newsletter(topic_input, marka_adi, uslup))
        else: st.warning("Konu giriniz.")

    # YENI: Video Senaryosu Butonu
    if b5.button("🎬 Video Script"):
        if len(topic_input) > 3:
            with st.spinner("Senaryo yazılıyor..."):
                script = generate_video_script(topic_input, marka_adi, uslup)
                st.warning("### 🎬 Reels/TikTok Senaryosu")
                st.write(script)
        else: st.warning("Konu giriniz.")