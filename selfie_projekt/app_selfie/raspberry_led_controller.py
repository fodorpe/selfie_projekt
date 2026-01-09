# raspberry_led_controller.py
import RPi.GPIO as GPIO
import time

class LEDController:
    def __init__(self):
        # GPIO pinek a 5 LED-hez (bármilyen szabad GPIO)
        self.led_pins = [17, 27, 22, 23, 24]  # 5 LED
        
        # PWM értékek (alacsony, hogy ne égjen ki a LED)
        self.pwm_values = [10, 15, 20, 25, 30]  # 10-30% között
        
        self.setup_gpio()
    
    def setup_gpio(self):
        """GPIO beállítása"""
        GPIO.setmode(GPIO.BCM)
        for pin in self.led_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
    
    def countdown_sequence(self, countdown_seconds=5):
        """
        Visszaszámlálás LED-ekkel
        5...4...3...2...1 = LED-ek sorban kialszanak
        """
        print(f"🚀 Visszaszámlálás indítása: {countdown_seconds} másodperc")
        
        # Először minden LED világít (alacsony fényerővel)
        for i, pin in enumerate(self.led_pins):
            self.set_led_pwm(pin, self.pwm_values[i])
        
        # Visszaszámlálás: LED-ek sorban kialszanak
        for second in range(countdown_seconds, 0, -1):
            print(f"  {second}...")
            
            # Melyik LED-et kell kikapcsolni?
            led_index = countdown_seconds - second
            
            if led_index < len(self.led_pins):
                # LED kikapcsolása
                GPIO.output(self.led_pins[led_index], GPIO.LOW)
                print(f"    LED {led_index + 1} ✨ KI")
            
            time.sleep(1)  # Vár 1 másodpercet
        
        # Minden LED ki
        self.all_off()
        print("🎉 MOSOLYOGJ! 😊")
        
        # Vár egy kicsit
        time.sleep(0.5)
        
        # Flash effekt: minden LED felvillan
        self.flash_all()
    
    def set_led_pwm(self, pin, duty_cycle):
        """LED PWM beállítása (biztonságos alacsony fényerő)"""
        try:
            # PWM létrehozása és beállítása
            pwm = GPIO.PWM(pin, 100)  # 100 Hz frekvencia
            pwm.start(duty_cycle)     # Duty cycle %
            time.sleep(0.1)
            pwm.stop()
            # Csak egy rövid ideig PWM-ezünk, utána LOW/High
            GPIO.output(pin, GPIO.HIGH if duty_cycle > 0 else GPIO.LOW)
        except:
            GPIO.output(pin, GPIO.HIGH if duty_cycle > 0 else GPIO.LOW)
    
    def flash_all(self, times=3, delay=0.2):
        """Minden LED villog"""
        print("✨ Flash effekt!")
        for _ in range(times):
            # Minden LED be
            for pin in self.led_pins:
                GPIO.output(pin, GPIO.HIGH)
            time.sleep(delay)
            
            # Minden LED ki
            for pin in self.led_pins:
                GPIO.output(pin, GPIO.LOW)
            time.sleep(delay)
    
    def all_off(self):
        """Minden LED kikapcsolása"""
        for pin in self.led_pins:
            GPIO.output(pin, GPIO.LOW)
    
    def cleanup(self):
        """GPIO takarítás"""
        self.all_off()
        GPIO.cleanup()
        print("🧹 GPIO takarítva")

# TESZT
if __name__ == "__main__":
    try:
        print("🎮 LED Controller indítása...")
        leds = LEDController()
        
        print("\n1. TESZT: Gyors villogás")
        leds.flash_all(times=2, delay=0.1)
        time.sleep(1)
        
        print("\n2. TESZT: Visszaszámlálás 5 másodperc")
        leds.countdown_sequence(5)
        
        time.sleep(2)
        
        print("\n3. TESZT: Visszaszámlálás 3 másodperc")
        leds.countdown_sequence(3)
        
    except KeyboardInterrupt:
        print("\n⏹️ Megszakítva")
    except Exception as e:
        print(f"❌ Hiba: {e}")
    finally:
        leds.cleanup()