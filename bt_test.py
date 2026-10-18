"""Проверка Bluetooth-соединения: печатает в консоль всё, что пришло с телефона,
и отвечает эхом ("ECHO: ...").

Запуск на Raspberry Pi:  python3 bt_test.py
"""

import time

from bluetooth_link import BluetoothLink


def main() -> None:
    bt = BluetoothLink(channel=1)
    bt.start()
    print("Сервер запущен (канал 1). Ожидание подключения телефона...")

    try:
        while True:
            address = bt.wait_for_client()
            print(f"[{time.strftime('%H:%M:%S')}] Подключён: {address}")
            bt.send("Привет от Raspberry Pi! Пришлите любую строку.")

            try:
                while True:
                    line = bt.receive_line(timeout=5)
                    if line is None:
                        print(f"[{time.strftime('%H:%M:%S')}] ...данных нет, соединение живо")
                        continue
                    print(f"[{time.strftime('%H:%M:%S')}] Получено: {line!r}")
                    bt.send(f"ECHO: {line}")
            except ConnectionError as e:
                print(f"[{time.strftime('%H:%M:%S')}] Отключён: {e}")
                print("Ожидание нового подключения...")
    except KeyboardInterrupt:
        print("\nВыход по Ctrl+C")
    finally:
        bt.close()


if __name__ == "__main__":
    main()
