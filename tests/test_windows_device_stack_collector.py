import json
import threading

from scripts.python.windows_device_stack.common import build_frame


def test_collect_frame_parses_serial_frame_into_unified_measurement():
    from scripts.python.windows_device_stack.edge_collector import collect_frame

    frame = build_frame(
        device_code="CAP-001",
        timestamp="2026-04-16T10:30:00",
        voltage=221.4,
        current=12.8,
        power=4.6,
        reactive_power=-2.3,
        power_factor=0.95,
        temperature=35.2,
        scene="normal",
    )

    measurement = collect_frame(frame, port="COM6", baudrate=9600)

    assert measurement["device_code"] == "CAP-001"
    assert measurement["timestamp"] == "2026-04-16T10:30:00"
    assert measurement["source"] == "rs485_collector"
    assert measurement["transport"] == "rs485"
    assert measurement["meta"] == {"scene": "normal", "port": "COM6", "baudrate": 9600}
    assert measurement["raw"]["frame"] == frame
    assert measurement["metrics"]["reactive_power"] == -2.3


def test_append_measurement_to_queue_writes_jsonl_record(tmp_path):
    from scripts.python.windows_device_stack.edge_collector import append_measurement_to_queue

    measurement = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 221.4,
            "current": 12.8,
            "power": 4.6,
            "reactive_power": -2.3,
            "power_factor": 0.95,
            "temperature": 35.2,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-001|...>", "crc_ok": True},
    }
    queue_file = tmp_path / "queue.jsonl"

    append_measurement_to_queue(measurement, queue_file)

    assert queue_file.read_text(encoding="utf-8") == json.dumps(measurement) + "\n"


def test_append_measurement_to_queue_appends_two_jsonl_records(tmp_path):
    from scripts.python.windows_device_stack.edge_collector import append_measurement_to_queue

    first = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 221.4,
            "current": 12.8,
            "power": 4.6,
            "reactive_power": -2.3,
            "power_factor": 0.95,
            "temperature": 35.2,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-001|...>", "crc_ok": True},
    }
    second = {
        "device_code": "CAP-002",
        "timestamp": "2026-04-16T10:30:01",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 222.4,
            "current": 13.1,
            "power": 4.9,
            "reactive_power": -2.1,
            "power_factor": 0.96,
            "temperature": 35.5,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-002|...>", "crc_ok": True},
    }
    queue_file = tmp_path / "queue.jsonl"

    append_measurement_to_queue(first, queue_file)
    append_measurement_to_queue(second, queue_file)

    assert queue_file.read_text(encoding="utf-8") == (
        json.dumps(first) + "\n" + json.dumps(second) + "\n"
    )


def test_append_measurement_to_queue_serializes_in_process_writers(tmp_path):
    from scripts.python.windows_device_stack.edge_collector import append_measurement_to_queue

    queue_file = tmp_path / "queue.jsonl"
    first = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 221.4,
            "current": 12.8,
            "power": 4.6,
            "reactive_power": -2.3,
            "power_factor": 0.95,
            "temperature": 35.2,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-001|...>", "crc_ok": True},
    }
    second = {
        "device_code": "CAP-002",
        "timestamp": "2026-04-16T10:30:01",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 222.4,
            "current": 13.1,
            "power": 4.9,
            "reactive_power": -2.1,
            "power_factor": 0.96,
            "temperature": 35.5,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-002|...>", "crc_ok": True},
    }

    results = []

    def write_measurement(measurement):
        append_measurement_to_queue(measurement, queue_file)
        results.append(True)

    first_thread = threading.Thread(target=write_measurement, args=(first,))
    second_thread = threading.Thread(target=write_measurement, args=(second,))

    first_thread.start()
    second_thread.start()
    first_thread.join()
    second_thread.join()

    assert len(results) == 2
    assert set(queue_file.read_text(encoding="utf-8").splitlines()) == {
        json.dumps(first),
        json.dumps(second),
    }


def test_append_measurement_to_queue_writes_once_and_flushes(tmp_path, monkeypatch):
    import scripts.python.windows_device_stack.edge_collector as edge_collector

    measurement = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 221.4,
            "current": 12.8,
            "power": 4.6,
            "reactive_power": -2.3,
            "power_factor": 0.95,
            "temperature": 35.2,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-001|...>", "crc_ok": True},
    }

    class FakeHandle:
        def __init__(self):
            self.write_calls = []
            self.flush_calls = 0
            self.fileno_calls = 0

        def write(self, text):
            self.write_calls.append(text)

        def flush(self):
            self.flush_calls += 1

        def fileno(self):
            self.fileno_calls += 1
            return 7

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    handle = FakeHandle()

    def fake_open(self, mode="r", encoding=None):
        return handle

    monkeypatch.setattr(edge_collector.Path, "open", fake_open, raising=False)

    append_measurement_to_queue = edge_collector.append_measurement_to_queue
    append_measurement_to_queue(measurement, tmp_path / "queue.jsonl")

    assert handle.write_calls == [json.dumps(measurement) + "\n"]
    assert handle.flush_calls == 1
    assert handle.fileno_calls >= 1


def test_append_measurement_to_queue_uses_posix_file_lock(tmp_path, monkeypatch):
    import scripts.python.windows_device_stack.edge_collector as edge_collector

    measurement = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 221.4,
            "current": 12.8,
            "power": 4.6,
            "reactive_power": -2.3,
            "power_factor": 0.95,
            "temperature": 35.2,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-001|...>", "crc_ok": True},
    }

    class FakeHandle:
        def __init__(self):
            self.write_calls = []
            self.flush_calls = 0
            self.fileno_calls = 0

        def write(self, text):
            self.write_calls.append(text)

        def flush(self):
            self.flush_calls += 1

        def fileno(self):
            self.fileno_calls += 1
            return 11

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeFcntl:
        LOCK_EX = 1
        LOCK_UN = 2

        def __init__(self):
            self.calls = []

        def flock(self, fd, flag):
            self.calls.append((fd, flag))

    handle = FakeHandle()
    fake_fcntl = FakeFcntl()
    fsync_calls = []

    def fake_open(self, mode="r", encoding=None):
        return handle

    monkeypatch.setattr(edge_collector, "fcntl", fake_fcntl, raising=False)
    monkeypatch.setattr(edge_collector, "msvcrt", None, raising=False)
    monkeypatch.setattr(edge_collector.os, "fsync", lambda fd: fsync_calls.append(fd))
    monkeypatch.setattr(edge_collector.Path, "open", fake_open, raising=False)

    edge_collector.append_measurement_to_queue(measurement, tmp_path / "queue.jsonl")

    assert fake_fcntl.calls == [(11, fake_fcntl.LOCK_EX), (11, fake_fcntl.LOCK_UN)]
    assert handle.write_calls == [json.dumps(measurement) + "\n"]
    assert handle.flush_calls == 1
    assert fsync_calls == [11]


def test_append_measurement_to_queue_uses_windows_file_lock(tmp_path, monkeypatch):
    import scripts.python.windows_device_stack.edge_collector as edge_collector

    measurement = {
        "device_code": "CAP-001",
        "timestamp": "2026-04-16T10:30:00",
        "source": "rs485_collector",
        "transport": "rs485",
        "metrics": {
            "voltage": 221.4,
            "current": 12.8,
            "power": 4.6,
            "reactive_power": -2.3,
            "power_factor": 0.95,
            "temperature": 35.2,
        },
        "meta": {"scene": "normal", "port": "COM6", "baudrate": 9600},
        "raw": {"frame": "<CAP-001|...>", "crc_ok": True},
    }

    class FakeHandle:
        def __init__(self):
            self.write_calls = []
            self.flush_calls = 0
            self.fileno_calls = 0
            self.seek_calls = []

        def write(self, text):
            self.write_calls.append(text)

        def flush(self):
            self.flush_calls += 1

        def fileno(self):
            self.fileno_calls += 1
            return 13

        def seek(self, offset, whence=0):
            self.seek_calls.append((offset, whence))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeMsvcrt:
        LK_LOCK = 3
        LK_UNLCK = 4

        def __init__(self):
            self.calls = []

        def locking(self, fd, flag, size):
            self.calls.append((fd, flag, size))

    handle = FakeHandle()
    fake_msvcrt = FakeMsvcrt()
    fsync_calls = []

    def fake_open(self, mode="r", encoding=None):
        return handle

    monkeypatch.setattr(edge_collector, "fcntl", None, raising=False)
    monkeypatch.setattr(edge_collector, "msvcrt", fake_msvcrt, raising=False)
    monkeypatch.setattr(edge_collector.os, "fsync", lambda fd: fsync_calls.append(fd))
    monkeypatch.setattr(edge_collector.Path, "open", fake_open, raising=False)

    edge_collector.append_measurement_to_queue(measurement, tmp_path / "queue.jsonl")

    assert fake_msvcrt.calls == [(13, fake_msvcrt.LK_LOCK, 1), (13, fake_msvcrt.LK_UNLCK, 1)]
    assert handle.seek_calls == [(0, 0), (0, 0)]
    assert handle.write_calls == [json.dumps(measurement) + "\n"]
    assert handle.flush_calls == 1
    assert fsync_calls == [13]
