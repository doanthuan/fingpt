import json

from utils.version_increment import increment_version, update_new_version


def test_increment_version():
    assert increment_version("0.0.1", "patch") == "0.0.2"
    assert increment_version("0.0.1", "minor") == "0.1.0"
    assert increment_version("0.0.1", "major") == "1.0.0"


def test_update_new_version():
    # create a test json file
    current_version = {"version": "0.0.1"}
    with open(".test.json", "w") as f:
        json.dump(current_version, f)
    update_new_version(".test.json", "patch")
    with open(".test.json", "r") as f:
        data = json.load(f)
        assert data["version"] == "0.0.2"
    # remove the test json file
    import os

    os.remove(".test.json")
