from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv

import joblib
import pandas as pd
import yfinance as yf
import os


# --------------------------------------------------
# 1. Ortam değişkenlerini yükle
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# 2. Flask uygulaması
# --------------------------------------------------

app = Flask(__name__)

CORS(app)


# --------------------------------------------------
# 3. Gemini API
# --------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("UYARI: GEMINI_API_KEY bulunamadı!")

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# --------------------------------------------------
# 4. Eğitilmiş modelleri yükle
# --------------------------------------------------

rf_model = joblib.load("risk_analiz_modeli.pkl")
le = joblib.load("label_encoder.pkl")


# --------------------------------------------------
# 5. Modelde kullanılan dönüşümler
# --------------------------------------------------

vade_map = {
    "short": 0,
    "medium": 1,
    "long": 2
}

tepki_map = {
    "sell": 0,
    "hold": 1,
    "buy": 2
}


# --------------------------------------------------
# 6. Sunucunun çalıştığını kontrol etmek için
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "FinanceAI API çalışıyor"
    })


# --------------------------------------------------
# 7. Ana analiz API'si
# --------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
def analyze():

    try:

        # JSON verisini al
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "JSON verisi gönderilmedi."
            }), 400


        # --------------------------------------------------
        # Gerekli alanları kontrol et
        # --------------------------------------------------

        gerekli_alanlar = [
            "age",
            "income",
            "horizon",
            "reaction",
            "ticker"
        ]

        for alan in gerekli_alanlar:

            if alan not in data:
                return jsonify({
                    "error": f"Eksik alan: {alan}"
                }), 400


        # --------------------------------------------------
        # Kullanıcı verilerini hazırla
        # --------------------------------------------------

        yas = int(data["age"])
        gelir = int(data["income"])

        horizon = data["horizon"]
        reaction = data["reaction"]

        ticker = str(data["ticker"]).strip().upper()


        # Geçerli seçenekleri kontrol et

        if horizon not in vade_map:
            return jsonify({
                "error": "Geçersiz yatırım vadesi."
            }), 400


        if reaction not in tepki_map:
            return jsonify({
                "error": "Geçersiz piyasa tepkisi."
            }), 400


        vade = vade_map[horizon]
        tepki = tepki_map[reaction]


        # --------------------------------------------------
        # 8. Model tahmini
        # --------------------------------------------------

        user_df = pd.DataFrame(
            [[yas, gelir, vade, tepki]],
            columns=[
                "Yas",
                "Gelir",
                "Vade",
                "Kriz_Tepkisi"
            ]
        )


        pred_encoded = rf_model.predict(user_df)[0]

        profil = le.inverse_transform(
            [pred_encoded]
        )[0]


        # --------------------------------------------------
        # 9. Risk profili açıklaması
        # --------------------------------------------------

        aciklama = (
            f"Yapay zekâ modelimiz sizi "
            f"<strong>{profil}</strong> bir yatırımcı "
            f"olarak sınıflandırdı. "
        )


        if profil == "Defansif":

            aciklama += (
                "Risk toleransınız düşük olduğu için, "
                "yüksek volatiliteye sahip hisselerden "
                "uzak durmanız ve daha güvenli varlıkları "
                "tercih etmeniz önerilir."
            )


        elif profil == "Dengeli":

            aciklama += (
                "Orta seviye risk alabiliyorsunuz. "
                "Portföyünüzü çeşitlendirerek hem güvenli "
                "hem de büyüme odaklı varlıklara yatırım "
                "yapabilirsiniz."
            )


        else:

            aciklama += (
                "Risk iştahınız yüksek. Uzun vadeli "
                "hedeflerle piyasadaki sert dalgalanmaları "
                "tolere edebilir ve potansiyel yüksek "
                "getiriler için daha riskli varlıkları "
                "değerlendirebilirsiniz."
            )


        # --------------------------------------------------
        # 10. Canlı hisse analizi
        # --------------------------------------------------

        try:

            stock = yf.Ticker(ticker)

            hist = stock.history(
                period="3mo"
            )


            if not hist.empty:

                max_price = hist["High"].max()
                min_price = hist["Low"].min()

                volatilite = (
                    (max_price - min_price)
                    / min_price
                ) * 100


                hisse_durumu = (
                    f"<strong>{ticker}</strong> hissesi "
                    f"son 3 ayda "
                    f"<strong>%{volatilite:.1f}</strong> "
                    f"fiyat aralığı dalgalanması göstermiştir."
                )


            else:

                hisse_durumu = (
                    f"{ticker} kodlu hisse bulunamadı. "
                    f"Türk hisseleri için örneğin "
                    f"THYAO.IS formatını kullanın."
                )


        except Exception as e:

            print("YFinance hatası:", e)

            hisse_durumu = (
                "Hisse verisi çekilirken "
                "bir piyasa hatası oluştu."
            )


        # --------------------------------------------------
        # 11. Gemini prompt
        # --------------------------------------------------

        prompt = f"""
Sen vizyoner, dürüst, samimi, günlük dil kullanan
ve gerçekçi bir yapay zekâ finans danışmanısın.

Kullanıcıya karmaşık borsa terimleri kullanmadan
açık ve anlaşılır şekilde cevap ver.

Karşındaki yatırımcının bilgileri:

- Yaş: {yas}
- Algoritmamızın belirlediği risk profili: {profil}
- İlgilendiği hisse kodu: {ticker}
- Hissenin piyasa durumu: {hisse_durumu}

Görevlerin:

1. Kullanıcının risk profili ile seçtiği hisse senedinin
   piyasa durumunu karşılaştır.

2. Eğer risk profili ile hisse arasında belirgin bir
   uyumsuzluk varsa kullanıcıyı uyar.

3. Kullanıcıya gerçekçi kısa bir stres senaryosu sun.

4. Doğrudan kullanıcıya hitap et.

5. Cevabını açık, günlük ve profesyonel bir dille
   yaklaşık 3 cümle halinde yaz.

Bu bir yatırım tavsiyesi değildir.
"""


        # --------------------------------------------------
        # 12. Gemini cevabı
        # --------------------------------------------------

        try:

            cevap = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=prompt
            )

            dinamik_tavsiye = cevap.text


        except Exception as e:

            hata_mesaji = str(e)

            print("Gemini hatası:", hata_mesaji)


            if (
                "429" in hata_mesaji
                or "quota" in hata_mesaji.lower()
            ):

                dinamik_tavsiye = (
                    "Günlük ücretsiz analiz limitimize "
                    "ulaştık. İlginiz için teşekkürler, "
                    "lütfen daha sonra tekrar deneyin."
                )

            else:

                dinamik_tavsiye = (
                    "Yapay zekâ danışmanı şu anda "
                    "yanıt veremiyor. Lütfen daha sonra "
                    "tekrar deneyin."
                )


        # --------------------------------------------------
        # 13. Frontend'e sonucu gönder
        # --------------------------------------------------

        return jsonify({

            "profil": profil,

            "aciklama": aciklama,

            "hisse_durumu": hisse_durumu,

            "tavsiye": dinamik_tavsiye

        })


    except ValueError:

        return jsonify({
            "error": "Yaş ve gelir sayısal olmalıdır."
        }), 400


    except Exception as e:

        print("Analiz hatası:", e)

        return jsonify({
            "error": "Analiz sırasında bir sunucu hatası oluştu."
        }), 500


# --------------------------------------------------
# LOCAL ÇALIŞTIRMA
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )