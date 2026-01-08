function bekapcsolKamera() {
            // Megkeressük a video elemet
            const video = document.getElementById('video');
            
            // Megpróbáljuk elérni a kamerát
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(function(stream) {
                    // Ha sikerült, beállítjuk a videó forrását
                    video.srcObject = stream;
                })
                .catch(function(error) {
                    // Ha nem sikerült, kiírjuk a hibát
                    alert("Hiba: " + error.message);
                });
        }





function combineImages() {
    const canvas = document.getElementById('canvas');
    const overlayImg = document.getElementById('overlayImage');
    const finalCanvas = document.getElementById('finalCanvas');
    const finalSection = document.querySelector('.final-section');
    
    if (!canvas || !overlayImg) return;
    
    // Méretek beállítása
    finalCanvas.width = canvas.width;
    finalCanvas.height = canvas.height;
    const ctx = finalCanvas.getContext('2d');
    
    // 1. Alapkép (a selfie)
    ctx.drawImage(canvas, 0, 0);
    
    // 2. Overlay kép (háttérként vagy átfedésként)
    try {
        // Átméretezés, hogy kitöltse a teljes területet
        ctx.drawImage(overlayImg, 0, 0, finalCanvas.width, finalCanvas.height);
        
        // 3. Visszajön a selfie (opcionális átlátszósággal)
        ctx.globalAlpha = 0.7; // Átlátszóság
        ctx.drawImage(canvas, 0, 0);
        ctx.globalAlpha = 1.0;
        
        // Végeredmény megjelenítése
        finalSection.style.display = 'block';
        
        // Base64 kódolás a küldéshez
        currentPhotoData = finalCanvas.toDataURL('image/jpeg', 0.8);
        
        alert("Kép készült a háttérrel!");
    } catch (e) {
        console.error("Hiba az összeolvasztásnál:", e);
        currentPhotoData = canvas.toDataURL('image/jpeg', 0.8);
    }
}

// Hívd meg a combineImages() függvényt a takePicture() függvény végén:
function takePicture() {
    // ... meglévő kód ...
    
    // Kép összeolvasztása a háttérképpel
    combineImages();
}