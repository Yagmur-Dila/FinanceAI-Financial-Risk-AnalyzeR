from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import yfinance as yf

app = Flask(__name__)
CORS(app) # HTML sayfamızın bu sunucuyla haberleşmesine izin verir

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
            aciklama += "Risk toleransınız düşük olduğu için, yüksek volatiliteye sahip hisselerden uzak durmanız ve daha güvenli limanlarda kalmanız önerilir."
        elif profil == 'Dengeli':
            aciklama += "Orta seviye risk alabiliyorsunuz. Portföyünüzü çeşitlendirerek hem güvenli hem de büyüme odaklı hisselere yönelebilirsiniz."
        else: # Agresif
            aciklama += "Risk iştahınız yüksek. Uzun vadeli hedeflerle piyasadaki sert dalgalanmaları tolere edebilir ve agresif büyüme fırsatlarını değerlendirebilirsiniz."

        # 5. Canlı Piyasa Analizi (yfinance ile)
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo") # Son 3 aylık veri
            if not hist.empty:
                max_price = hist['High'].max()
                min_price = hist['Low'].min()
                volatilite = ((max_price - min_price) / min_price) * 100
                hisse_durumu = f"<strong>{ticker}</strong> hissesi son 3 ayda <strong>%{volatilite:.1f}</strong> oranında dalgalanma (risk) göstermiştir."
            else:
                hisse_durumu = f"{ticker} kodlu hisse bulunamadı. (Türk hisseleri için sonuna .IS ekleyin, örn: THYAO.IS)"
        except:
            hisse_durumu = "Hisse verisi çekilirken bir piyasa hatası oluştu."

        # 6. Sonucu HTML'e Gönderme
        return jsonify({
            'profil': profil,
            'aciklama': aciklama,
            'hisse_durumu': hisse_durumu
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)