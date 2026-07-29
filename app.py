from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import yfinance as yf
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # HTML sayfamızın bu sunucuyla haberleşmesine izin verir

# --- YENİ: Gemini API Ayarları ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-3.5-flash')

# 1. Eğittiğimiz Modelleri Yükleme
rf_model = joblib.load('risk_analiz_modeli.pkl')
le = joblib.load('label_encoder.pkl')

# Metinleri sayılara çevirme sözlükleri (Eğitimdekiyle birebir aynı olmalı)
vade_map = {'short': 0, 'medium': 1, 'long': 2}
tepki_map = {'sell': 0, 'hold': 1, 'buy': 2}


@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json

        # 2. Kullanıcıdan Gelen Verileri Sayısallaştırma
        yas = int(data['age'])
        gelir = int(data['income'])
        vade = vade_map[data['horizon']]
        tepki = tepki_map[data['reaction']]
        ticker = data['ticker']

        # 3. Model Tahmini
        user_df = pd.DataFrame([[yas, gelir, vade, tepki]], columns=['Yas', 'Gelir', 'Vade', 'Kriz_Tepkisi'])
        pred_encoded = rf_model.predict(user_df)[0]
        profil = le.inverse_transform([pred_encoded])[0]

        # 4. Açıklanabilir AI (Explainable AI) Metni 
        aciklama = f"Yapay zekâ modelimiz sizi '<strong>{profil}</strong>' bir yatırımcı olarak sınıflandırdı. "
        if profil == 'Defansif':
            aciklama += "Risk toleransınız düşük olduğu için, yüksek volatiliteye sahip hisselerden uzak durmanız ve güvenli limanları tercih etmeniz önerilir."
        elif profil == 'Dengeli':
            aciklama += "Orta seviye risk alabiliyorsunuz. Portföyünüzü çeşitlendirerek hem güvenli hem de büyüme odaklı varlıklara yatırım yapabilirsiniz."
        else:  # Agresif
            aciklama += "Risk iştahınız yüksek. Uzun vadeli hedeflerle piyasadaki sert dalgalanmaları tolere edebilir, potansiyel yüksek getiriler için riskli varlıklara yönelebilirsiniz."

        # 5. Canlı Piyasa Analizi (yfinance ile)
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")  # Son 3 aylık veri
            if not hist.empty:
                max_price = hist['High'].max()
                min_price = hist['Low'].min()
                volatilite = ((max_price - min_price) / min_price) * 100
                hisse_durumu = f"<strong>{ticker}</strong> hissesi son 3 ayda <strong>%{volatilite:.1f}</strong> dalgalanma göstermiştir."
            else:
                hisse_durumu = f"{ticker} kodlu hisse bulunamadı. (Türk hisseleri için sonuna .IS ekleyin, örn: THYAO.IS)"
        except:
            hisse_durumu = "Hisse verisi çekilirken bir piyasa hatası oluştu."

        # 6. Gemini Yapay Zekâ Danışman (YENİ EKLENEN DİNAMİK MOTOR)
        prompt = f"""
        Sen vizyoner, dürüst, samimi, günlük dil kullanan ve gerçekçi bir yapay zekâ finans danışmanısın. Lütfen kullanıcılara karmaşık borsa terimleri ('spekülatif', 'vahşi dinamikler' vb.) kullanmadan, gayet günlük, sade bir dil kullan tıpkı bir arkadaşa tavsiye veriyormuş gibi.

        Karşındaki yatırımcının bilgileri:
        - Yaş: {yas}
        - Bizim Algoritmamızın Belirlediği Risk Profili: {profil}
        - İlgilendiği Hisse Kodu: {ticker}
        - Hissenin Piyasa Durumu: {hisse_durumu}

        Görevlerin:
        1. Uyumsuzluk Analizi: Kullanıcının risk profili ile seçtiği hisse senedinin piyasa durumunu çarpıştır. Eğer bir zıtlık varsa uyar.
        2. Stres Testi: Kullanıcıya gerçekçi bir senaryo sun.
        3. Çıktı Formatı: Doğrudan kullanıcıya hitap et ("Sen" veya "Siz" diliyle). Sadece 3 cümlelik, akıcı, gündelik ve profesyonel bir tavsiye metni yaz. Merhaba, saygılar gibi gereksiz kelimeler kullanma. Sadece tavsiyeyi ver.
        """

        try:
            cevap = gemini_model.generate_content(prompt)
            dinamik_tavsiye = cevap.text
            
        except Exception as e:
            hata_mesaji = str(e)
            
            # Eğer hata mesajında 429 veya quota (kota) kelimesi geçiyorsa:
            if "429" in hata_mesaji or "quota" in hata_mesaji.lower():
                dinamik_tavsiye = "Günlük ücretsiz analiz limitimize ulaştık. İlginiz için çok teşekkürler, lütfen yarın tekrar deneyin! 😊"
                
            # Eğer API'de anlık başka bir yoğunluk veya çökme olursa:
            else:
                dinamik_tavsiye = f"SİSTEM HATASI: {hata_mesaji}"

        # 7. Sonucu HTML'e Gönderme (Artık 'tavsiye' değişkenini de yolluyoruz)
        return jsonify({
            'profil': profil,
            'aciklama': aciklama,
            'hisse_durumu': hisse_durumu,
            'tavsiye': dinamik_tavsiye
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)