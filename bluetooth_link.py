"""Приём и отправка данных по Bluetooth (классический RFCOMM / SPP).

Работает на Raspberry Pi (Linux), внешних библиотек не нужно —
используется встроенный в Python сокет AF_BLUETOOTH.

Подготовка Raspberry Pi (один раз):
    sudo sdptool add --channel=1 SP      # объявить Serial Port Profile
    bluetoothctl -> power on, discoverable on, pairable on, agent on
Затем сопрягите телефон и подключитесь приложением
"Serial Bluetooth Terminal" (или своим) к Raspberry Pi.
"""

import socket


class BluetoothLink:
    def __init__(self, channel: int = 1, encoding: str = "utf-8"):
        self.channel = channel
        self.encoding = encoding
        self._server = None
        self._client = None
        self._buffer = b""

    # --- жизненный цикл -------------------------------------------------
    def start(self) -> None:
        """Открыть серверный сокет и начать слушать."""
        self._server = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        self._server.bind((socket.BDADDR_ANY, self.channel))
        self._server.listen(1)

    def wait_for_client(self) -> str:
        """Блокируется до подключения телефона. Возвращает его MAC-адрес."""
        if self._server is None:
            self.start()
        self._client, (address, _) = self._server.accept()
        self._buffer = b""
        return address

    @property
    def connected(self) -> bool:
        return self._client is not None

    def close_client(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None
                self._buffer = b""

    def close(self) -> None:
        self.close_client()
        if self._server is not None:
            self._server.close()
            self._server = None

    # --- обмен данными --------------------------------------------------
    def receive_line(self, timeout: float | None = None) -> str | None:
        """Читает одну строку (до '\\n').

        Возвращает None, если за timeout секунд строка не пришла.
        Бросает ConnectionError, если телефон отключился.
        """
        if self._client is None:
            raise ConnectionError("Клиент не подключён")

        self._client.settimeout(timeout)
        while b"\n" not in self._buffer:
            try:
                chunk = self._client.recv(1024)
            except socket.timeout:
                return None
            except OSError as e:
                self.close_client()
                raise ConnectionError(str(e)) from e
            if not chunk:
                self.close_client()
                raise ConnectionError("Телефон отключился")
            self._buffer += chunk

        line, self._buffer = self._buffer.split(b"\n", 1)
        return line.decode(self.encoding, errors="ignore").strip()

    def send(self, text: str) -> None:
        """Отправляет строку телефону (добавляет '\\n')."""
        if self._client is None:
            raise ConnectionError("Клиент не подключён")
        try:
            self._client.sendall((text + "\n").encode(self.encoding))
        except OSError as e:
            self.close_client()
            raise ConnectionError(str(e)) from e
