async function generateKey() {
    const appNameInput = document.getElementById('appName');
    const name = appNameInput.value.trim();
    const btn = document.getElementById('generateBtn');

    if (!name) {
        alert("Lütfen bir uygulama adı girin.");
        return;
    }

    const originalText = btn.innerText;
    btn.innerText = "Oluşturuluyor...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name })
        });

        if (!response.ok) {
            throw new Error('API Hatası');
        }

        const data = await response.json();
        
        document.getElementById('apiKeyText').innerText = data.key;
        document.getElementById('resultBox').classList.remove('hidden');
        
        appNameInput.value = ''; // temizle
    } catch (err) {
        alert("Hata oluştu: " + err.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

async function copyKey() {
    const keyText = document.getElementById('apiKeyText').innerText;
    if (!keyText) return;
    
    try {
        await navigator.clipboard.writeText(keyText);
        const hint = document.querySelector('.copy-hint');
        hint.innerText = "Kopyalandı! ✓";
        hint.style.color = "var(--accent)";
        
        setTimeout(() => {
            hint.innerText = "Kopyalamak için tıklayın";
            hint.style.color = "var(--text-muted)";
        }, 2000);
    } catch (err) {
        alert("Kopyalanamadı.");
    }
}
