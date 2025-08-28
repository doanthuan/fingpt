import json
import sys


def increment_version(version: str = "0.0.1", part: str = "patch") -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError("Invalid part. Use 'major', 'minor', or 'patch'")

    return f"{major}.{minor}.{patch}"


def update_new_version(file_path: str, part: str = "patch") -> None:
    with open(file_path, "r") as f:
        data = json.load(f)
        current_version = data["version"]
        new_version = increment_version(current_version, part)

    data["version"] = new_version
    with open(file_path, "w") as f:
        json.dump(data, f)

    print(f"Updated version from {current_version} to {new_version}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python version_increment.py <file_path> <part>")
        sys.exit(1)
    version_path = sys.argv[1]
    part = sys.argv[2]
    update_new_version(version_path, part)
