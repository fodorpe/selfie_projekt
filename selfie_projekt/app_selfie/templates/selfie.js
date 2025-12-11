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