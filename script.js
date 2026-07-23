document.getElementById('riskForm').addEventListener('submit', async function(e) {
    e.preventDefault(); 
    
    // Form verilerini toplama
    const userData = {
        age: document.getElementById('age').value,
        income: document.getElementById('income').value,
        horizon: document.getElementById('horizon').value,
        reaction: document.getElementById('reaction').value,
        ticker: document.getElementById('ticker').value.toUpperCase()
    };


    const resultArea = document.getElementById('resultArea');
    if (yas < 1 || yas > 100) {
    alert("Lütfen geçerli bir yaş giriniz.");
    return; // Hata varsa işlemi burada durdurur, sunucuya boşuna istek atmaz.
}
    resultArea.style.display = 'block';
    resultArea.style.backgroundColor = '#e0f7fa';
    resultArea.innerHTML = "AI Modeli Piyasa Verilerini Çekiyor ve Analiz Ediyor... ⏳";

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
        resultArea.innerHTML = `
            <h3 style="margin-top: 0; color: #1a4f8b;">Profiliniz: ${result.profil} 🎯</h3>
            <p style="font-weight: normal; margin-bottom: 10px; line-height: 1.5;">${result.aciklama}</p>
            <hr style="border: 0; border-top: 1px solid rgba(0,0,0,0.1); margin: 15px 0;">
            <p style="font-weight: normal; font-size: 0.95em;">📊 <strong>Piyasa Notu:</strong> ${result.hisse_durumu}</p>
        `;

    } catch (error) {
        resultArea.style.backgroundColor = '#ffcdd2';
        resultArea.innerHTML = "Sunucuya bağlanılamadı. Python (Flask) sunucusunun çalıştığından emin olun.";
        console.error("Hata:", error);
    }
});