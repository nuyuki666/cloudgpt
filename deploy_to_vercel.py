# deploy_to_vercel.py
# Automated Vercel Deployer for CloudGPT Mobile
import os
import sys
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def deploy_via_api(token, project_name="cloudgpt-mobile"):
    print(f"[*] Deploying CloudGPT to Vercel (Project: {project_name})...")
    
    files_payload = []
    
    # 1. Read vercel.json
    vercel_json = (BASE_DIR / "vercel.json").read_text(encoding="utf-8")
    files_payload.append({
        "file": "vercel.json",
        "data": vercel_json,
        "encoding": "utf-8"
    })
    
    # 2. Read requirements.txt
    req_txt = (BASE_DIR / "requirements.txt").read_text(encoding="utf-8")
    files_payload.append({
        "file": "requirements.txt",
        "data": req_txt,
        "encoding": "utf-8"
    })

    # 3. Read api/index.py
    api_index = (BASE_DIR / "api" / "index.py").read_text(encoding="utf-8")
    files_payload.append({
        "file": "api/index.py",
        "data": api_index,
        "encoding": "utf-8"
    })

    # 4. Read public files
    public_dir = BASE_DIR / "public"
    for p in public_dir.glob("*"):
        if p.is_file():
            rel_name = f"public/{p.name}"
            if p.suffix in [".png", ".jpg", ".ico"]:
                import base64
                b64_data = base64.b64encode(p.read_bytes()).decode("utf-8")
                files_payload.append({
                    "file": rel_name,
                    "data": b64_data,
                    "encoding": "base64"
                })
            else:
                text_data = p.read_text(encoding="utf-8")
                files_payload.append({
                    "file": rel_name,
                    "data": text_data,
                    "encoding": "utf-8"
                })

    payload = {
        "name": project_name,
        "files": files_payload,
        "projectSettings": {
            "framework": None
        }
    }

    req = urllib.request.Request(
        "https://api.vercel.com/v13/deployments",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            url = data.get("url")
            print("\n" + "=" * 60)
            print("  [SUCCESS] DEPLOYED TO VERCEL!")
            print(f"  -> Production URL: https://{url}")
            print("=" * 60)
            return f"https://{url}"
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Vercel API returned {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    if not token and len(sys.argv) > 1:
        token = sys.argv[1].strip()

    if not token:
        print("=" * 60)
        print("  [*] VERCEL DEPLOYMENT INSTRUCTIONS:")
        print("=" * 60)
        print("  1. Вы можете задеплоить репозиторий через GitHub:")
        print("     - Перейдите на https://vercel.com/new")
        print("     - Импортируйте ваш репозиторий (все настройки в vercel.json уже готовы)")
        print("     - Нажмите 'Deploy'")
        print("-" * 60)
        print("  2. Или задеплоить прямо из консоли с токеном Vercel:")
        print("     python deploy_to_vercel.py <ВАШ_ТОКЕН_VERCEL>")
        print("=" * 60)
        return

    deploy_via_api(token)


if __name__ == "__main__":
    main()
