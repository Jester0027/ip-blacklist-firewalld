from typing import List

import requests
import subprocess
import sys
import os
import tempfile

IPSET_NAME = os.getenv('IPSET_NAME') or 'blocked_ips'
BLACKLISTED_IPS_URL = os.getenv('BLACKLISTED_IPS_URL') or 'https://raw.githubusercontent.com/stamparm/ipsum/refs/heads/master/levels/3.txt'

def run_firewall_cmd(*args: tuple) -> str:
    result = subprocess.run(
        ["firewall-cmd", *args],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()


def read_desired_entries(url: str) -> set[str]:
    response = requests.get(url)
    
    if response.status_code >= 400:
        raise RuntimeError(response.text)
        
    return set(response.text.splitlines())


def ensure_ipset_exists(ipset: str, type: str = 'hash:ip') -> None:
    result = subprocess.run(
        ["firewall-cmd", "--get-ipsets", "--permanent"],
        capture_output=True,
        text=True,
        check=True,
    )

    existing = set(result.stdout.split())

    if ipset not in existing:
        print(f"Creating ipset '{ipset}'...")
        run_firewall_cmd(
            "--permanent",
            "--new-ipset", ipset,
            "--type", type,
        )
        run_firewall_cmd("--reload")


def get_current_entries(ipset: str) -> set[str]:
    """Read current entries from firewalld."""
    output = run_firewall_cmd("--permanent", "--ipset", ipset, "--get-entries")

    if not output:
        return set()

    return set(output.splitlines())


def add_entries(ipset: str, entries: List[str]) -> None:
    if(len(entries) == 0):
        return

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as file:
        file.write("\n".join(entries))
        file.flush()
        run_firewall_cmd("--permanent", "--ipset", ipset, "--add-entries-from-file", file.name)


def remove_entries(ipset: str, entries: List[str]) -> None:
    if(len(entries) == 0):
        return

    with tempfile.NamedTemporaryFile(mode="w", delete=True) as file:
        file.write("\n".join(entries))
        file.flush()
        run_firewall_cmd("--permanent", "--ipset", ipset, "--remove-entries-from-file", file.name)


def get_zone_sources(zone: str) -> set[str]:
    output = run_firewall_cmd("--zone", zone, "--list-sources")

    if not output:
        return set()

    return set(output.split())


def ensure_ipset_in_zone(ipset: str, zone: str = "drop") -> None:
    sources = get_zone_sources(zone)
    source = f"ipset:{ipset}"

    if source not in sources:
        print(f"Adding {source} to zone '{zone}'...")
        run_firewall_cmd(
            "--permanent",
            "--zone", zone,
            "--add-source", source,
        )


def main() -> None:
    ensure_ipset_exists(IPSET_NAME)
    desired = read_desired_entries(BLACKLISTED_IPS_URL)
    current = get_current_entries(IPSET_NAME)

    to_add = desired - current
    to_remove = current - desired

    print(f"Current entries : {len(current)}")
    print(f"Desired entries : {len(desired)}")
    print(f"Adding          : {len(to_add)}")
    print(f"Removing        : {len(to_remove)}")

    add_entries(IPSET_NAME, sorted(to_add))
    remove_entries(IPSET_NAME, sorted(to_remove))

    ensure_ipset_in_zone(IPSET_NAME, zone="drop")

    run_firewall_cmd("--reload")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
