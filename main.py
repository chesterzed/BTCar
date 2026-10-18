"""Главный класс: принимает команды с телефона по Bluetooth и управляет мотором.

Протокол (текстовые строки, каждая заканчивается переводом строки):
    SPEED <0-100>   - задать скорость в процентах
    STOP            - остановить мотор
    STATUS          - узнать текущую скорость
"""

from bluetooth_link import BluetoothLink
from hdd_motor import HDDMotor


class RaspCar:
    def __init__(self, motor_pin: int = 18, bt_channel: int = 1, idle_timeout: float = 2.0):
        self.bt = BluetoothLink(channel=bt_channel)
        self.motor = HDDMotor(pin=motor_pin)
        # Если команд нет дольше idle_timeout секунд — мотор останавливается
        self.idle_timeout = idle_timeout
        self._running = False

    def handle_command(self, line: str) -> str:
        parts = line.upper().split()
        if not parts:
            return "ERR empty"

        cmd = parts[0]
        if cmd == "SPEED" and len(parts) == 2:
            try:
                self.motor.set_speed(float(parts[1]))
            except ValueError:
                return "ERR bad speed"
            return f"OK {self.motor.speed:.0f}"
        if cmd == "STOP":
            self.motor.stop()
            return "OK 0"
        if cmd == "STATUS":
            return f"SPEED {self.motor.speed:.0f}"
        return "ERR unknown command"

    def run(self) -> None:
        self._running = True
        self.motor.arm()
        self.bt.start()
        print("Ожидание подключения телефона...")
        try:
            while self._running:
                address = self.bt.wait_for_client()
                print(f"Подключён: {address}")
                self._serve_client()
                self.motor.stop()  # телефон отключился — безопасная остановка
                print("Клиент отключён")
        except KeyboardInterrupt:
            print("Остановка по Ctrl+C")
        finally:
            self.shutdown()

    def _serve_client(self) -> None:
        while self._running:
            try:
                line = self.bt.receive_line(timeout=self.idle_timeout)
                if line is None:  # тишина — глушим мотор
                    self.motor.stop()
                    continue
                self.bt.send(self.handle_command(line))
            except ConnectionError:
                return

    def shutdown(self) -> None:
        self._running = False
        self.motor.close()
        self.bt.close()


if __name__ == "__main__":
    RaspCar(motor_pin=18).run()
