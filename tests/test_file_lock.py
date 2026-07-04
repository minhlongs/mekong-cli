import json
import threading
import time
from src.core.file_lock import locked_read, locked_read_write

def test_file_lock_concurrency(tmp_path):
    file_path = tmp_path / "missions.json"
    file_path.write_text(json.dumps({"missions": []}))

    errors = []

    def writer_thread(tid):
        for i in range(20):
            try:
                with locked_read_write(file_path) as f:
                    content = f.read()
                    data = json.loads(content) if content else {}
                    missions = data.get("missions", [])
                    missions.append({"thread_id": tid, "index": i})
                    
                    f.seek(0)
                    f.write(json.dumps({"missions": missions}, indent=2))
                    f.truncate()
            except Exception as e:
                errors.append(f"Writer {tid} error: {e}")
            time.sleep(0.005)

    def reader_thread(tid):
        for i in range(20):
            try:
                with locked_read(file_path) as f:
                    content = f.read()
                    if content:
                        data = json.loads(content)
                        _ = data.get("missions", [])
            except Exception as e:
                errors.append(f"Reader {tid} error: {e}")
            time.sleep(0.005)

    threads = []
    for t in range(5):
        threads.append(threading.Thread(target=writer_thread, args=(t,)))
        threads.append(threading.Thread(target=reader_thread, args=(t,)))

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert not errors, f"Errors occurred during concurrent read/write: {errors}"
    
    with open(file_path, "r") as f:
        data = json.loads(f.read())
        assert len(data.get("missions", [])) == 100
