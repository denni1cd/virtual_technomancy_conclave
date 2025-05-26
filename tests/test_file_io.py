import threading
from pathlib import Path

import pytest

from conclave.tools import file_io

CONTENT_1 = "first writer\n"
CONTENT_2 = "second writer – wins!\n"


def test_concurrent_write_and_read(tmp_path: Path):
    """Two threads write concurrently; last one wins; data is intact."""
    target = tmp_path / "data.txt"

    def writer(text: str):
        file_io.write_file(target, text, mode="w")

    t1 = threading.Thread(target=writer, args=(CONTENT_1,))
    t2 = threading.Thread(target=writer, args=(CONTENT_2,))

    t1.start(), t2.start()
    t1.join(), t2.join()

    # final read should see a *complete* write, not interleaved fragments
    data = file_io.read_file(target)
    assert data in (CONTENT_1, CONTENT_2)
    assert data.count("\n") == 1


def test_read_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        file_io.read_file(tmp_path / "nope.txt")
