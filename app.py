import streamlit as st
from openai import OpenAI
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI SEO", layout="wide")

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
    
    # YENI OZELLIK: Üslup Seçimi
    uslup = st.selectbox(
        "Marka Dili (Üslup)", 
        ["Kurumsal ve Profesyonel", "Samimi ve Eğlenceli", "Bilimsel ve Teknik", "İkna Edici ve Satış Odaklı"]
    )
    
    st.info("Marka ve Sektör girmezseniz analiz çalışmaz.")

# 3. YAPAY ZEKA FONKSIYONLARI

def get_ai_suggestions(brand, sector):
    # 5 Konu + Anahtar Kelime + Rakip Analizi
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
    # Marka Karnesi + Reçete
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

def write_full_article(topic, brand, tone):
    # Makale Yazari (Üslup destekli)
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
    # Yeni Özellik: Sosyal Medya Paketi
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
    # Yeni Özellik: E-Bülten Modülü
    prompt = f"""
    Konu: "{topic}". Marka: {brand}. Üslup: {tone}.
    
    Bu blog yazısını, mevcut müşterilere gönderilecek profesyonel bir E-Bülten (Email Newsletter) formatına çevir.
    
    Format Şöyle Olsun:
    1. **Konu Satırı:** (İlgi çekici, tıklanma oranı yüksek bir başlık)
    2. **Selamlama:** (Kişiselleştirilmiş giriş)
    3. **Giriş:** (Sorunu tanımla)
    4. **Gelişme:** (Blog yazısındaki çözümün özeti)
    5. **Çağrı (CTA):** (Ürünü denemeye veya blog yazısının tamamını okumaya yönlendir)
    
    Lütfen kısa, net ve mobil uyumlu paragraflar kullan.
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
    
    # Buton 1: Genel Analiz
    if st.button("🚀 Detaylı SEO Analizi Yap"):
        if not marka_adi or not sektor:
            st.error("Lütfen önce sol menüden Marka ve Sektör girin!")
        else:
            with st.spinner("Rakipler inceleniyor..."):
                sonuc = get_ai_suggestions(marka_adi, sektor)
                st.markdown(sonuc)
                st.success("Analiz tamamlandı!")

    st.markdown("---") 

    # Buton 2: Marka Karnesi
    if st.button("🤖 AI Marka Karnesini Çıkar"):
        if not marka_adi or not sektor:
            st.error("Lütfen marka ve sektör girin!")
        else:
            with st.spinner("ChatGPT markanızı araştırıyor..."):
                karne = get_ai_brand_awareness(marka_adi, sektor)
                st.info("### 📢 Yapay Zeka Gözünde Markanız")
                st.write(karne)
                st.warning("Aşağıdaki 'Altın Konuları' kopyalayıp yandaki panele yapıştırın! 👉")

with col2:
    st.success("✍️ **2. Adım: İçerik Üretimi**")
    topic_input = st.text_area("Hangi konuyu yazalım?", placeholder="Soldaki analizden bir başlık kopyalayıp buraya yapıştırın...")
    
   # 3 butonu yan yana diziyoruz
    b1, b2, b3 = st.columns([1,1,1])
    
    if b1.button("Makaleyi Yaz"):
        if not topic_input or len(topic_input) < 5:
            st.warning("Konu giriniz.")
        else:
            with st.spinner("Makale yazılıyor..."):
                if not marka_adi: marka_adi = "Genel"
                article = write_full_article(topic_input, marka_adi, uslup)
                st.markdown(article)
                st.download_button("💾 Makaleyi İndir", article, file_name="seo-makale.md")

    if b2.button("Sosyal Medya Paketi"):
        if not topic_input or len(topic_input) < 5:
            st.warning("Önce bir konu giriniz.")
        else:
            with st.spinner("Postlar hazırlanıyor..."):
                posts = write_social_media_posts(topic_input, marka_adi, uslup)
                st.info("### 📱 Sosyal Medya İçerikleri")
                st.write(posts)

    if b3.button("📧 E-Bülten Hazırla"):
        if not topic_input or len(topic_input) < 5:
            st.warning("Önce bir konu giriniz.")
        else:
            with st.spinner("Mail taslağı yazılıyor..."):
                newsletter = write_newsletter(topic_input, marka_adi, uslup)
                st.success("### 📧 E-Bülten Taslağı")
                st.write(newsletter)