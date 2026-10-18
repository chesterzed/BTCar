"""Управление мотором от жёсткого диска (HDD spindle, бесколлекторный).

ВАЖНО: мотор HDD трёхфазный, напрямую от GPIO он не крутится.
Нужен драйвер/ESC (например, обычный авиамодельный регулятор), у которого
управляющий вход подключается к одному GPIO-пину Raspberry Pi:
    ESC signal -> GPIO (по умолчанию 18)
    ESC GND    -> GND Raspberry Pi
    ESC power  -> отдельное питание, 3 фазы ESC -> 3 вывода мотора

Управление идёт импульсами 1000–2000 мкс (как у серво) через pigpio —
он формирует сигнал аппаратно, без дрожания.
    sudo apt install pigpio python3-pigpio
    sudo systemctl enable --now pigpiod
"""

import time

import pigpio


class HDDMotor:
    def __init__(
        self,
        pin: int = 18,
        min_pulse: int = 1000,
        max_pulse: int = 2000,
        arm_time: float = 2.0,
    ):
        self.pin = pin
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.arm_time = arm_time
        self._speed = 0
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Не удалось подключиться к pigpiod (sudo systemctl start pigpiod)")

    @property
    def speed(self) -> int:
        return self._speed

    def arm(self) -> None:
        """Инициализация ESC: минимальный импульс на пару секунд."""
        self._pi.set_servo_pulsewidth(self.pin, self.min_pulse)
        time.sleep(self.arm_time)
        self._speed = 0

    def set_speed(self, percent: float) -> None:
        """Скорость 0..100 %."""
        percent = max(0.0, min(100.0, float(percent)))
        pulse = self.min_pulse + (self.max_pulse - self.min_pulse) * percent / 100
        self._pi.set_servo_pulsewidth(self.pin, int(pulse))
        self._speed = percent

    def stop(self) -> None:
        self.set_speed(0)

    def close(self) -> None:
        """Остановить мотор и освободить пин."""
        try:
            self._pi.set_servo_pulsewidth(self.pin, 0)  # 0 = выключить сигнал
        finally:
            self._pi.stop()
