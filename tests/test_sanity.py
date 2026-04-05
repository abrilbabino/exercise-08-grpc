from pathlib import Path

def test_proto_exists():
    assert Path("proto/node_registry.proto").exists()
def test_makefile_exists():
    assert Path("Makefile").exists()