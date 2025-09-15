#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from typing import Optional


def find_profile_dir_by_display_name(display_name: str) -> Optional[str]:
    """
    On macOS, map a Chrome profile display name (e.g. "telecomdesign.fr")
    to its internal directory name (e.g. "Profile 2" or "Default").
    """
    local_state_path = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome/Local State"
    )

    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    info_cache = (
        data.get("profile", {}).get("info_cache")
        if isinstance(data, dict)
        else None
    )
    if not isinstance(info_cache, dict):
        return None

    # Prefer exact match on the visible profile name.
    for dir_name, info in info_cache.items():
        if isinstance(info, dict) and info.get("name") == display_name:
            return dir_name

    # Secondary match on gaia_name or user_name if present.
    for dir_name, info in info_cache.items():
        if not isinstance(info, dict):
            continue
        if info.get("gaia_name") == display_name or info.get("user_name") == display_name:
            return dir_name

    return None


def launch_chrome_with_profile(profile_dir: str) -> int:
    chrome_binary = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    args = [chrome_binary, f"--profile-directory={profile_dir}"]

    try:
        subprocess.Popen(args)
        return 0
    except FileNotFoundError:
        # Fallback to macOS 'open' in case the direct binary path changes.
        try:
            subprocess.Popen([
                "open", "-na", "Google Chrome", "--args", f"--profile-directory={profile_dir}"
            ])
            return 0
        except Exception as e:
            print(f"Failed to launch Chrome via 'open': {e}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Failed to launch Chrome: {e}", file=sys.stderr)
        return 1


def main() -> None:
    # Desired visible profile name; can be overridden by first CLI argument.
    desired_display_name = sys.argv[1] if len(sys.argv) > 1 else "telecomdesign.fr"

    resolved_dir = find_profile_dir_by_display_name(desired_display_name)
    if resolved_dir:
        sys.exit(launch_chrome_with_profile(resolved_dir))

    # If not found, avoid creating a new profile silently. Show options.
    print(
        "Chrome profile not found by display name: '"
        + desired_display_name
        + "'.",
        file=sys.stderr,
    )
    # List available profiles to help the user adjust quickly.
    local_state_path = os.path.expanduser(
        "~/Library/Application Support/Google/Chrome/Local State"
    )
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        info_cache = data.get("profile", {}).get("info_cache", {})
        if isinstance(info_cache, dict) and info_cache:
            print("Available profiles:")
            for dir_name, info in info_cache.items():
                name = info.get("name") if isinstance(info, dict) else None
                print(f"- {dir_name} (name: {name})")
    except Exception:
        pass

    # Do not create a new profile unintentionally; exit with error.
    sys.exit(2)


if __name__ == "__main__":
    main()
