#!/usr/bin/env python3
import subprocess
import re
import sys
import os
import time
if os.name == "nt":
    print("Fail2Ban is not supported on Windows. Use WSL or Linux.")
    sys.exit(1)
print(os.name)

from i18n import I18N, ensure_lang_file



lang, lerr = ensure_lang_file()
i18n = I18N(lang)
t = i18n.t


def cls(clear=True):
    if clear == False:return
    os.system("clear")


def print_logo():
    print(rf"""
 ███████╗ █████╗ ██╗██╗     ██████╗ ██████╗  █████╗ ███╗   ██╗
 ██╔════╝██╔══██╗██║██║     ██╔══██╗██╔══██╗██╔══██╗████╗  ██║
 █████╗  ███████║██║██║     ██████╔╝██████╔╝███████║██╔██╗ ██║
 ██╔══╝  ██╔══██║██║██║     ██╔══██╗██╔══██╗██╔══██║██║╚██╗██║
 ██║     ██║  ██║██║███████╗██████╔╝██║  ██║██║  ██║██║ ╚████║
 ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝

        {t("app.title")}{f"\n        Locate error: {lerr}" if lerr != None else ""}
    """)

def is_admin():
    if os.name != "nt":return os.geteuid() == 0
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def run(cmd):
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or res.stdout.strip())
    return res.stdout


def get_jails():
    out = run(["fail2ban-client", "status"])
    m = re.search(r"Jail list:\s*(.+)", out)
    if not m:
        return []
    return [j.strip() for j in m.group(1).split(",") if j.strip()]


def ban_ip(jail, ip):
    run(["fail2ban-client", "set", jail, "banip", ip])


def unban_ip(jail, ip):
    run(["fail2ban-client", "set", jail, "unbanip", ip])


def banned_in_jails(ip):
    result = []
    for jail in get_jails():
        out = run(["fail2ban-client", "status", jail])
        if ip in out:
            result.append(jail)
    return result


def all_banned_ips():
    bans = {}

    for jail in get_jails():
        out = run(["fail2ban-client", "status", jail])

        for line in out.splitlines():
            if "Banned IP list:" in line:
                ips = line.split(":", 1)[1].strip().split()
                for ip in ips:
                    bans.setdefault(ip, []).append(jail)

    return bans


def select_jail():
    jails = get_jails()
    if not jails:
        print(t("common.no_jails"))
        return None

    print(f"\n0. {t("common.blocked_all")}")
    for i, jail in enumerate(jails, 1):
        print(f"{i}. {jail}")

    while True:
        c = input(f"{t("menu.choice")}: ").strip()
        if c == "0":
            return "ALL"
        if c.isdigit() and 1 <= int(c) <= len(jails):
            return jails[int(c) - 1]


def parse_duration_to_seconds(s: str) -> int:
    """
    Разбирает строки вроде:
      3600
      10m
      1h30m
      2d
    Возвращает число секунд.
    """
    s = s.strip().lower()
    if not s:
        raise ValueError("Пустая длительность")

    # если просто число — секунды
    if re.fullmatch(r"\d+", s):
        return int(s)

    # поддержим комбинации, например 1h30m
    total = 0
    for amount, unit in re.findall(r"(\d+)([smhdw]?)", s):
        n = int(amount)
        if unit == "" or unit == "s":
            total += n
        elif unit == "m":
            total += n * 60
        elif unit == "h":
            total += n * 3600
        elif unit == "d":
            total += n * 86400
        elif unit == "w":
            total += n * 604800
    if total == 0:
        raise ValueError("Не удалось разобрать длительность")
    return total


def get_bantime(jail):
    try:
        out = run(["fail2ban-client", "get", jail, "bantime"])
        # out может содержать просто число или строку с пояснением — постараемся извлечь число
        m = re.search(r"-?\d+", out)
        if m:
            return int(m.group(0))
    except Exception:
        pass
    return None


def set_bantime(jail, seconds):
    # seconds может быть отрицательным для вечного бана (-1)
    run(["fail2ban-client", "set", jail, "bantime", str(seconds)])


def ban_menu():
    ip = input("IP: ").strip()
    if not ip:
        print("IP не введён")
        input(t("common.press_enter"))
        return

    jail = select_jail()
    if jail is None:
        input(t("common.press_enter"))
        return

    # спросим, вечный или временный бан
    while True:
        choice = input(t("ban.type")).strip()
        # choice = input("Тип бана — (1) Временный, (2) Вечный (пока не разбанят): ").strip()
        if choice in ("1", "2"):
            break
    if choice == "2":
        # вечный
        if jail == "ALL":
            originals = {}
            for j in get_jails():
                try:
                    originals[j] = get_bantime(j)
                    try:
                        set_bantime(j, -1)
                    except Exception:
                        # если не удалось изменить bantime — всё равно попытаемся банить
                        pass
                    ban_ip(j, ip)
                except Exception as e:
                    print(t("error.ban.message", j=j, e=e))
                finally:
                    # восстановим оригинальный bantime, если был получен
                    if j in originals and originals[j] is not None:
                        try:
                            set_bantime(j, originals[j])
                        except Exception:
                            pass
            print(t("ban.success.perm.all", ip=ip))
        else:
            orig = get_bantime(jail)
            try:
                if orig is not None:
                    try:
                        set_bantime(jail, -1)
                    except Exception:
                        pass
                ban_ip(jail, ip)
                print(t("ban.success.perm.single", ip=ip, jail=jail))

            except Exception as e:
                print(f"\n{t("error.message", e=e)}")
            finally:
                if orig is not None:
                    try:
                        set_bantime(jail, orig)
                    except Exception:
                        pass
    else:
        # временный бан — спросим длительность
        dur = input(t("input.duration")).strip()
        try:
            secs = parse_duration_to_seconds(dur)
        except Exception as e:
            print(f"Не удалось распознать длительность: {e}")
            input(t("common.press_enter"))
            return

        if jail == "ALL":
            originals = {}
            for j in get_jails():
                try:
                    originals[j] = get_bantime(j)
                    try:
                        set_bantime(j, secs)
                    except Exception:
                        pass
                    ban_ip(j, ip)
                except Exception as e:
                    print(t("error.ban.message", j=j, e=e))
                finally:
                    if j in originals and originals[j] is not None:
                        try:
                            set_bantime(j, originals[j])
                        except Exception:
                            pass
            print(f"\nIP {ip} заблокирован на {secs} секунд во всех jail (по возможности).")
        else:
            orig = get_bantime(jail)
            try:
                if orig is not None:
                    try:
                        set_bantime(jail, secs)
                    except Exception:
                        pass
                ban_ip(jail, ip)
                print(f"\nIP {ip} заблокирован в jail {jail} на {secs} секунд")
            except Exception as e:
                print(f"\nОшибка: {e}")
            finally:
                if orig is not None:
                    try:
                        set_bantime(jail, orig)
                    except Exception:
                        pass

    input(t("common.press_enter"))


def unban_menu():
    ip = input(f"{t("input.ip")}: ").strip()
    jails = banned_in_jails(ip)

    if not jails:
        print(f"\n{t("unban.not_banned")}\n")
    else:
        for jail in jails:
            unban_ip(jail, ip)
        print(f"\n{t("unban.success", ip=ip)}\n")

    input(t("common.press_enter"))




def show_all_bans():
    bans = all_banned_ips()

    if not bans:
        print(f"\n{t("show_all.error.not_have_active_bans")}\n")
    else:
        print(f"\n{t("show_all.success.active_bans")}:\n")
        for ip, jails in sorted(bans.items()):
            print(f"{ip}")
            for jail in jails:
                print(f"  - {jail}")
            print()

    input(t("common.press_enter"))


def check_ip_firewall(ip):
    """Проверка блокировки IP на уровне firewall (nftables/iptables)."""
    try:
        out = subprocess.check_output(["nft", "list", "ruleset"], text=True, stderr=subprocess.DEVNULL)
        if ip in out:
            return True
    except Exception:
        pass
    try:
        out = subprocess.check_output(["iptables", "-L", "-n"], text=True, stderr=subprocess.DEVNULL)
        if ip in out:
            return True
    except Exception:
        pass
    return False


def check_ip_status():
    """Проверка статуса IP: в каких jail и на уровне firewall."""
    ip = input(f"{t("input.ip")}: ").strip()
    jails = banned_in_jails(ip)
    # print(jails)
    fw_blocked = check_ip_firewall(ip)
    # print(fw_blocked)

    if not jails and not fw_blocked:
        print(f"\n{t("check.not_found", ip=ip)}\n")
        input(t("common.press_enter"))
        return

    if jails:
        print(f"\n{t("check.jails", ip=ip)}:")
        for j in jails:
            print(f" - {j}")
    else:
        print(f"\n{t("check.jails.not_found", ip=ip)}")

    if fw_blocked:
        print(f"{t("check.success.firewall")}")
    else:
        print(f"{t("check.fail.firewall")}")
    input(t("common.press_enter"))


def preflight_check():
    if not is_admin():
        print(t("error.message", e="Script must be run as root"))
        sys.exit(1)
    try:
        run(["fail2ban-client", "ping"])
    except Exception as e:
        print(t("error.message", e=f"fail2ban-client not responding: {e}"))
        sys.exit(1)
    try:
        jails = get_jails()
    except Exception as e:
        print(t("error.message", e=f"Unable to get jail list: {e}"))
        sys.exit(1)
    if not jails:
        print(t("common.no_jails"))
        sys.exit(1)
    return True


def main():
    cls(False)
    print_logo()
    time.sleep(1)

    while True:
        cls()
        print_logo()
        print(f"""
1. {t("menu.ban")}
2. {t("menu.unban")}
3. {t("menu.check")}
4. {t("menu.show_all")}
5. {t("menu.exit")}
""")

        try:c = input(f"{t("menu.choice")}: ").strip()
        except KeyboardInterrupt:break

        try:
            if c == "1":
                cls()
                print_logo()
                ban_menu()
            elif c == "2":
                cls()
                print_logo()
                unban_menu()
            elif c == "3":
                cls()
                print_logo()
                check_ip_status()
            elif c == "4":
                cls()
                print_logo()
                show_all_bans()
            elif c == "5":
                cls()
                sys.exit(0)
        except Exception as e:
            print(f"\n{t("error.message", e=e)}\n")


if __name__ == "__main__":
    preflight_check()
    main()