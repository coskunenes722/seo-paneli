import streamlit as st
from openai import OpenAI
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Yapay Zeka SEO Paneli", layout="wide")

# --- PROFESYONEL GIRIS SISTEMI ---
# Kullanici Adi : Sifre
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
    # Marka Karnesi (Bilinirlik Testi)
    prompt = f"""
    Sen bir Yapay Zeka Denetçisisin. "{brand}" markasını {sector} sektöründe analiz et.
    Bana şu formatta kısa bir rapor ver:
    1. **Bilinirlik Skoru:** (0 ile 100 arasında bir puan ver. Eğer marka çok yeniyse düşük ver.)
    2. **Yapay Zeka Görüşü:** (ChatGPT olarak bu marka hakkında ne biliyorsun? Olumlu/Olumsuz/Nötr mü?)
    3. **Eksik Gedik:** (Bu markanın yapay zekada daha iyi tanınması için hangi konularda içerik üretmesi lazım?)
    Lütfen samimi ve gerçekçi ol.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def write_full_article(topic, brand):
    # Makale Yazari
    prompt = f"""
    Konu: {topic}. Marka: {brand}. 
    600 kelimelik, SEO uyumlu, teknik bir blog yazısı yaz.
    - İçinde mutlaka bir HTML tablosu olsun.
    - Alt başlıklar (h2, h3) kullan.
    - İçeriğin en altına JSON-LD formatında Schema (FAQ) kodu ekle.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Sen {brand} markası için çalışan profesyonel bir içerik yazarısın."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

# 4. ANA SAYFA TASARIMI
st.title("🚀 Yapay Zeka SEO Paneli")

col1, col2 = st.columns([1,1])

with col1:
    st.info("🕵️ **1. Adım: Analiz & Strateji**")
    
    # Buton 1: Genel Analiz
    if st.button("🚀 Detaylı SEO Analizi Yap"):
        if not marka_adi or not sektor:
            st.error("Lütfen önce sol menüden Marka ve Sektör girin!")
        else:
            with st.spinner("Rakipler inceleniyor, kelimeler bulunuyor..."):
                sonuc = get_ai_suggestions(marka_adi, sektor)
                st.markdown(sonuc)
                st.success("Analiz tamamlandı!")

    st.markdown("---") 

    # Buton 2: Marka Karnesi (Yeni Özellik)
    if st.button("🤖 AI Marka Karnesini Çıkar"):
        if not marka_adi or not sektor:
            st.error("Lütfen marka ve sektör girin!")
        else:
            with st.spinner("ChatGPT markanızı araştırıyor..."):
                karne = get_ai_brand_awareness(marka_adi, sektor)
                st.info("### 📢 Yapay Zeka Gözünde Markanız")
                st.write(karne)
                st.warning("Puanınız düşükse, yandaki panelden makale yazdırarak yapay zekayı eğitebilirsiniz!")

with col2:
    st.success("✍️ **2. Adım: Makale Yaz**")
    topic_input = st.text_area("Hangi konuyu yazalım?", placeholder="Soldaki analizden bir başlık kopyalayıp buraya yapıştırın...")
    
    if st.button("Makaleyi Yaz"):
        if not topic_input or len(topic_input) < 5:
            st.warning("Lütfen geçerli bir konu başlığı girin.")
        else:
            with st.spinner("Makale yazılıyor, lütfen bekleyin..."):
                if not marka_adi:
                    marka_adi = "Genel"
                article = write_full_article(topic_input, marka_adi)
                st.markdown(article)
                st.download_button("💾 Makaleyi İndir", article, file_name="seo-makale.md")