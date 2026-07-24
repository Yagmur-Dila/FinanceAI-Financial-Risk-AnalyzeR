const form = document.getElementById('riskForm');
const resultArea = document.getElementById('resultArea');

function getErrorElement(fieldId) {
    return document.getElementById(fieldId + 'Error');
}

function clearErrors() {
    const fields = ['age', 'income', 'horizon', 'reaction', 'ticker'];
    fields.forEach(fieldId => {
        const errorElement = getErrorElement(fieldId);
        const inputElement = document.getElementById(fieldId);
        if (errorElement) errorElement.textContent = '';
        if (inputElement) inputElement.classList.remove('input-error');
    });
    resultArea.style.display = 'none';
}

function setError(fieldId, message) {
    const errorElement = getErrorElement(fieldId);
    const inputElement = document.getElementById(fieldId);
    if (errorElement) errorElement.textContent = message;
    if (inputElement) inputElement.classList.add('input-error');
}

document.getElementById('riskForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    clearErrors();

    const ageValue = document.getElementById('age').value.trim();
    const incomeValue = document.getElementById('income').value.trim();
    const horizonValue = document.getElementById('horizon').value;
    const reactionValue = document.getElementById('reaction').value;
    const tickerValue = document.getElementById('ticker').value.trim().toUpperCase();

    let hasError = false;

    if (ageValue === '') {
        setError('age', 'Lütfen bu alanı boş bırakmayınız.');
        hasError = true;
    } else if (isNaN(Number(ageValue)) || Number(ageValue) < 1 || Number(ageValue) > 100) {
        setError('age', 'Lütfen geçerli bir yaş giriniz.');
        hasError = true;
    }

    if (incomeValue === '') {
        setError('income', 'Lütfen bu alanı boş bırakmayınız.');
        hasError = true;
    }

    if (horizonValue === '') {
        setError('horizon', 'Lütfen bu alanı boş bırakmayınız.');
        hasError = true;
    }

    if (reactionValue === '') {
        setError('reaction', 'Lütfen bu alanı boş bırakmayınız.');
        hasError = true;
    }

    if (tickerValue === '') {
        setError('ticker', 'Lütfen bu alanı boş bırakmayınız.');
        hasError = true;
    }

    if (hasError) {
        const firstInvalid = form.querySelector('.input-error');
        if (firstInvalid) firstInvalid.focus();
        return;
    }

    const userData = {
        age: ageValue,
        income: incomeValue,
        horizon: horizonValue,
        reaction: reactionValue,
        ticker: tickerValue
    };

    resultArea.style.display = 'block';
    resultArea.style.backgroundColor = '#e0f7fa';
    resultArea.innerHTML = 'AI Modeli Piyasa Verilerini Çekiyor ve Analiz Ediyor... ⏳';

    try {
        // Flask Python sunucumuza (API) verileri gönderiyoruz
        const response = await fetch('https://financeai-financial-risk-analyzer.onrender.com/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });

        const result = await response.json();

        if(result.error) {
            resultArea.innerHTML = "Bir hata oluştu: " + result.error;
            resultArea.style.backgroundColor = '#ffcdd2';
            return;
        }

        // Çıkan profile göre arayüz rengini değiştirme
        let renk = '#c8e6c9'; // Defansif (Yeşil - Güvenli)
        if (result.profil === 'Dengeli') renk = '#fff9c4'; // Sarı
        if (result.profil === 'Agresif') renk = '#ffcdd2'; // Kırmızı (Riskli)

        resultArea.style.backgroundColor = renk;
        
        
        // Gelen detaylı AI açıklamasını ve canlı hisse verisini ekrana basma
        resultArea.innerHTML =`
    <h3 style="margin-top: 0; color: #1a4f8b;">Profiliniz: ${result.profil} 🎯</h3>
    <p style="font-weight: normal; margin-bottom: 10px; line-height: 1.5;">${result.aciklama}</p>
    
    <hr style="border: 0; border-top: 1px solid rgba(0,0,0,0.1); margin: 15px 0;">
    <p style="font-weight: normal; font-size: 0.95em; margin-bottom: 15px;">📊 <strong>Piyasa Notu:</strong> ${result.hisse_durumu}</p>
    
    <div style="background-color: rgba(255,255,255,0.5); padding: 12px; border-radius: 8px; border-left: 4px solid #1a4f8b;">
        <strong style="color: #1a4f8b;">🤖 Yapay Zekâ Danışman:</strong><br>
        <span style="font-size: 0.95em; line-height: 1.6; color: #333;">${result.tavsiye}</span>
    </div>
`;

    } catch (error) {
        resultArea.style.backgroundColor = '#ffcdd2';
        resultArea.innerHTML = "Sunucuya bağlanılamadı. Python (Flask) sunucusunun çalıştığından emin olun.";
        console.error("Hata:", error);
    }
});