# push_to_github.py
# Automated GitHub Uploader for CloudGPT
import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
GIT_PATH = BASE_DIR / "apk_tools" / "mingit" / "cmd" / "git.exe"
GIT = str(GIT_PATH) if GIT_PATH.exists() else "git"


def run_cmd(cmd, cwd=str(BASE_DIR)):
    print(f"[GIT] Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr and res.returncode != 0:
        print(f"[ERROR] {res.stderr.strip()}")
    return res.returncode == 0


def setup_and_push(repo_url):
    print("=" * 60)
    print("  [*] PUSHING CLOUDGPT REPOSITORY TO GITHUB")
    print("=" * 60)
    print(f"  Target Repository: {repo_url}")
    print("-" * 60)

    # 1. Check/Init Git
    git_dir = BASE_DIR / ".git"
    if not git_dir.exists():
        run_cmd([GIT, "init"])

    # 2. Config user
    run_cmd([GIT, "config", "user.name", "CloudGPT-Developer"])
    run_cmd([GIT, "config", "user.email", "cloudgpt@local.dev"])

    # 3. Add and commit
    run_cmd([GIT, "add", "-A"])
    run_cmd([GIT, "commit", "-m", "Initial commit: CloudGPT Mobile App, Vercel Serverless API, and Android APK"])

    # 4. Set branch main
    run_cmd([GIT, "branch", "-M", "main"])

    # 5. Set remote origin
    run_cmd([GIT, "remote", "remove", "origin"])
    run_cmd([GIT, "remote", "add", "origin", repo_url])

    # 6. Push
    print("\n[*] Pushing to origin main...")
    success = run_cmd([GIT, "push", "-u", "origin", "main", "--force"])
    
    if success:
        print("\n" + "=" * 60)
        print("  [SUCCESS] PROJECT SUCCESSFULLY UPLOADED TO GITHUB!")
        print(f"  -> Repo: {repo_url}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  [TIP] Если требуется авторизация GitHub:")
        print("  Используйте токен GitHub в URL:")
        print("  https://<ВАШ_ТОКЕН>@github.com/<USERNAME>/<REPO>.git")
        print("=" * 60)


def main():
    if len(sys.argv) > 1:
        repo_url = sys.argv[1].strip()
        setup_and_push(repo_url)
    else:
        print("=" * 60)
        print("  [*] ИНСТРУКЦИЯ ПО ВЫГРУЗКЕ НА GITHUB:")
        print("=" * 60)
        print("  1. Создайте новый репозиторий на https://github.com/new (например, 'cloudgpt')")
        print("  2. Скопируйте ссылку на репозиторий.")
        print("  3. Запустите команду:")
        print("     python push_to_github.py https://github.com/<ВАШ_НИК>/<ИМЯ_РЕПО>.git")
        print("-" * 60)
        print("  Или если у вас есть GitHub Personal Access Token:")
        print("     python push_to_github.py https://<TOKEN>@github.com/<ВАШ_НИК>/<ИМЯ_РЕПО>.git")
        print("=" * 60)


if __name__ == "__main__":
    main()
