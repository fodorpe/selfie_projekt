# raspberry_led_safe.py - BIZTONSÁGOS verzió ellenállással
import RPi.GPIO as GPIO
import time

class SafeLEDController:
    def __init__(self):
        # GPIO pinek
        self.led_pins = [17, 27, 22, 23, 24]
        
        # Ellenállás mellett lehet nagyobb fényerő
        self.brightness = 70  # 70% (ellenállással biztonságos)
        
        self.setup_gpio()
    
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in self.led_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
    
    def countdown(self, seconds=5):
        """Visszaszámlálás LED-ekkel"""
        print(f"🔴 Visszaszámlálás: {seconds} másodperc")
        
        # Minden LED bekapcsolása
        for pin in self.led_pins:
            GPIO.output(pin, GPIO.HIGH)
        
        # LED-ek sorban kikapcsolása
        for i in range(seconds):
            remaining = seconds - i
            print(f"  {remaining}...")
            
            if i < len(self.led_pins):
                GPIO.output(self.led_pins[i], GPIO.LOW)
            
            time.sleep(1)
        
        # "MOSOLYOGJ!" üzenet
        print("😊 MOSOLYOGJ!")
        self.all_off()
        time.sleep(0.5)
        
        # Flash effekt
        self.celebrate()
    
    def celebrate(self):
        """Ünneplés flash effekttel"""
        print("🎉 Ünneplés!")
        
        # 3x villanás
        for _ in range(3):
            for pin in self.led_pins:
                GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.15)
            
            for pin in self.led_pins:
                GPIO.output(pin, GPIO.LOW)
            time.sleep(0.15)
        
        # Futó fény effekt
        print("🌈 Futó fény...")
        for _ in range(2):  # 2x ismétlés
            for pin in self.led_pins:
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(pin, GPIO.LOW)
        
        # Utolsó nagy flash
        for pin in self.led_pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.3)
        self.all_off()
    
    def all_off(self):
        for pin in self.led_pins:
            GPIO.output(pin, GPIO.LOW)
    
    def cleanup(self):
        self.all_off()
        GPIO.cleanup()

# Webes integrációhoz
class WebLEDController(SafeLEDController):
    """Webes felülethez integrálható LED vezérlő"""
    
    def web_countdown(self, duration=5):
        """Webből hívható visszaszámlálás"""
        import threading
        
        def run_countdown():
            self.countdown(duration)
        
        # Szálban futtatjuk, hogy ne blokkolja a web szervert
        thread = threading.Thread(target=run_countdown)
        thread.start()
        return thread