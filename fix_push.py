# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import urllib.request
import json

GH_USER = "dmitNCh"
GH_REPO = "kubkod-apk"

print("======================================================")
print(" ИСПРАВЛЕНИЕ БЛОКИРОВКИ ANDROID И ОТПРАВКА НА GITHUB")
print("======================================================")
token = input("Вставьте ваш GitHub Token (github_pat_... или ghp_...): ").strip()

if not token:
    print("[!] Токен не введен!")
    exit(1)

# 1. Пробуем автоматически создать репозиторий на GitHub через API
print("\n[1/3] Создание репозитория kubkod-apk на GitHub...")
req = urllib.request.Request(
    "https://api.github.com/user/repos",
    data=json.dumps({"name": GH_REPO, "private": False}).encode("utf-8"),
    method="POST"
)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/vnd.github+json")
req.add_header("Content-Type", "application/json")
req.add_header("User-Agent", "Termux-App")

try:
    with urllib.request.urlopen(req) as resp:
        print(" [+] Репозиторий kubkod-apk успешно создан!")
except urllib.error.HTTPError as e:
    if e.code == 422:
        print(" [+] Репозиторий kubkod-apk уже существует на вашем аккаунте.")
    else:
        print(f" [!] Внимание (код {e.code}): Ваш токен не имеет прав создавать репозитории автоматически.")
        print("     Если вы еще не создали репозиторий вручную, откройте https://github.com/new")
        print("     назовите его kubkod-apk и нажмите Create repository.")

# 2. Копируем проект в родную память Termux (где нет ошибки dubious ownership)
print("\n[2/3] Перенос файлов в безопасную рабочую область Termux...")
src = "/storage/emulated/0/Download/04_APK_КУБКОД_ДАТЧИКИ"
work = os.path.expanduser("~/kubkod_clean_repo")

if os.path.exists(work):
    shutil.rmtree(work)
shutil.copytree(src, work)

dot_git = os.path.join(work, ".git")
if os.path.exists(dot_git):
    shutil.rmtree(dot_git)

# 3. Инициализация и отправка
print("\n[3/3] Отправка кода на GitHub...")
cmds = [
    ["git", "init"],
    ["git", "branch", "-M", "main"],
    ["git", "config", "user.name", GH_USER],
    ["git", "config", "user.email", f"{GH_USER}@users.noreply.github.com"],
    ["git", "add", "."],
    ["git", "commit", "-m", "KUBKOD-125 APK Real-Time Sensor Filter"],
    ["git", "remote", "add", "origin", f"https://oauth2:{token}@github.com/{GH_USER}/{GH_REPO}.git"],
    ["git", "push", "-u", "origin", "main", "--force"]
]

push_ok = True
for cmd in cmds:
    res = subprocess.run(cmd, cwd=work, capture_output=True, text=True)
    if res.returncode != 0:
        print(" [!] Ошибка на шаге:", " ".join(cmd[:2]))
        print(res.stderr.strip())
        push_ok = False
        break

if push_ok:
    print("\n======================================================")
    print(" [УСПЕХ!] ВСЕ ФАЙЛЫ ЗАГРУЖЕНЫ НА GITHUB!")
    print(" Теперь откройте в браузере телефона:")
    print(f" https://github.com/{GH_USER}/{GH_REPO}/actions")
    print("======================================================")
else:
    print("\n======================================================")
    print(" [!] ПОЧЕМУ GITHUB НЕ ПРИНЯЛ ФАЙЛЫ:")
    print(" 1. Либо репозиторий 'kubkod-apk' еще не создан вручную на https://github.com/new")
    print(" 2. Либо ваш Fine-grained токен (github_pat_...) создан без права записи (Read-only).")
    print(" РЕШЕНИЕ: На странице токенов выберите вкладку 'Tokens (classic)',")
    print(" нажмите 'Generate new token (classic)', поставьте галочки 'repo' и 'workflow'")
    print(" и вставьте сюда полученный токен (он начинается на ghp_...).")
    print("======================================================")
