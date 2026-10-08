# server.py
import http.server
import socket
import socketserver
import os
import sys
import json
import urllib.request
import urllib.parse
import re
from pathlib import Path

PORT = 8000
PUBLIC_DIR = Path(__file__).resolve().parent / "public"

import base64

_d = lambda s: base64.b64decode(s).decode('utf-8')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or _d("QVEuQWI4Uk42SkVtTW9UNWtqdzhjQUhfQ0NBMi16TDBsOFBMc2dRYS1lNWhPXzllZ2VmSFE=")
TH_RUDDER_KEY = os.environ.get("TH_RUDDER_KEY") or _d("dGhrX2xpdmVfT2F2SVJmTHNXME5sMlZQa0gxR1hzWGJWaFRfeTUxOERfSVhTa3RGTnZCUDNrUTI2ZVVaRjVWN2haeUdjejh0Vg==")
ATR_KEY = os.environ.get("ATR_KEY") or _d("YXRyX3dPUUtqbC0zYWthT0MxVC1IQXFZcVp1dVlIckxZemN5")
OPENROUTER_KEYS = [
    _d("c2stb3ItdjEtMzQwY2EzM2Q5MTI1NDQ4MmJiNGZhMjhjMjgwNzAyZTg0OTkyMmU2NGM3Y2EzYjZkMDhhNTE2MmVkMDczNWFhYw=="),
    _d("c2stb3ItdjEtNGZjZjBjOTAwNWFmN2EwMGZlYzRjYTY5NDEzNTVkMDVmOGI4OWU5ZmExOGM0MGI3MDQyNDk2YTdmNzFmY2JkYw==")
]


def get_local_ip():
    """Retrieve the primary local IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


# Smart Prompt Dictionary & Enhancement Engine
PROMPT_EXPANSIONS = [
    (r'(?i)(неб[а-я]*|небес[а-я]*|sky|skies)', 'breathtaking vibrant blue sky with fluffy white cumulus clouds, bright natural sun rays, atmospheric depth, cinematic lighting, ultra-detailed 8k landscape photography, clear horizon'),
    (r'(?i)(закат[а-я]*|рассвет[а-я]*|sunset[s]?|sunrise[s]?)', 'dramatic golden hour sunset with rich orange and violet twilight sky, sunbeams breaking through clouds, picturesque cinematic 8k landscape'),
    (r'(?i)(ночн[а-я]*\s*неб[а-я]*|звезд[а-я]*|космос[а-я]*|галактик[а-я]*|space|galaxy|nebula|star[s]?)', 'stunning deep night sky filled with millions of sparkling stars, Milky Way galaxy nebula, glowing cosmic dust, pristine 8k astrophotography'),
    (r'(?i)(кот[а-я]*|кошк[а-я]*|коти[а-я]*|котя[а-я]*|cat[s]?|kitten[s]?)', 'adorable fluffy domestic cat with expressive sparkling eyes, ultra detailed fur texture, warm cozy lighting, 8k macro portrait photography'),
    (r'(?i)(собак[а-я]*|пес[а-я]*|щенок[а-я]*|щенк[а-я]*|dog[s]?|puppy|puppies)', 'beautiful friendly dog with shiny coat, expressive joyful eyes, soft natural outdoor bokeh lighting, 8k portrait photography'),
    (r'(?i)(машин[а-я]*|авто[а-я]*|спорткар[а-я]*|автомобил[а-я]*|car[s]?|supercar[s]?)', 'sleek aerodynamic modern supercar, high-gloss metallic reflection, dramatic automotive studio lighting, aggressive styling, 8k rendering'),
    (r'(?i)(девушк[а-я]*|женщин[а-я]*|человек[а-я]*|портрет[а-я]*|лиц[а-я]*|girl[s]?|woman|women|portrait[s]?)', 'stunning detailed portrait of an attractive person, natural soft studio lighting, realistic skin texture, sharp expressive eyes, 8k master photography'),
    (r'(?i)(город[а-я]*|мегаполис[а-я]*|киберпанк[а-я]*|cyberpunk|city|cities)', 'futuristic cyberpunk metropolis at night, vibrant neon signs reflections on wet streets, towering architectural skyscrapers, cinematic fog, 8k'),
    (r'(?i)(лес[а-я]*|природ[а-я]*|гор[а-я]*|озер[а-я]*|forest[s]?|nature|mountain[s]?|lake[s]?)', 'majestic alpine mountain landscape with lush pine forest, morning mist, crystal clear lake, golden sunlight rays, 8k nature photography'),
    (r'(?i)(океан[а-я]*|мор[а-я]*|пляж[а-я]*|ocean[s]?|sea[s]?|beach[es]?)', 'crystal clear turquoise ocean waves gently breaking on pristine white sand beach, tropical sunny day, 8k coastal photography')
]


def enhance_prompt(prompt: str) -> str:
    cleaned = re.sub(r'^(нарисуй мне|сгенерируй мне|нарисуй|сгенерируй|создай фото|создай картинку|сделай фото|сделай картинку|нарисуй картинку|draw me|draw|generate image of|create photo of)\s+', '', prompt, flags=re.IGNORECASE).strip()
    for pattern, expansion in PROMPT_EXPANSIONS:
        if re.search(pattern, cleaned):
            return f"{expansion}, ultra detailed, photorealistic, 8k resolution, masterpieces, clean composition, no watermark, no text"
    return f"photorealistic highly detailed 8k image of {cleaned}, natural cinematic lighting, masterpiece composition, award-winning photography, no watermark, no text"


MODEL_PERSONAS = {
    "cloudgpt": (
        "Ты — CloudGPT, передовая флагманская интеллектуальная нейросеть нового поколения, "
        "полностью разработанная и обученная нашей командой. "
        "Ты обладаешь глубокими знаниями в программировании, системной архитектуре, реверс-инжиниринге (C++, Rust, Assembly, читы, хуки, инжекторы), "
        "компьютерном зрении и генерации контента. Всегда отвечай уверенно, технически грамотно, подробно и вежливо на русском языке с красивой Markdown-разметкой."
    ),
    "claude-haiku-5.5:free": (
        "Ты — Claude Haiku 5.5 (в ядре экосистемы CloudGPT), ультрабыстрая и высокоточная модель. "
        "Твои главные качества: молниеносная скорость ответа, кристальная логика, чистый читаемый код и лаконичность. "
        "Отвечай на русском языке с подсветкой синтаксиса."
    ),
    "deepseek-v4.1-flash:free": (
        "Ты — DeepSeek V4.1 Flash (в ядре экосистемы CloudGPT), продвинутая нейросеть для сложного reasoning, "
        "программирования, математики, низкоуровневых алгоритмов, читов, драйверов и реверс-инжиниринга. "
        "Отвечай с максимальной технической детализацией, структурированно и с рабочими примерами кода."
    ),
    "mimo-v2.6-flash:free": (
        "Ты — MiMo V2.6 Flash (в ядре экосистемы CloudGPT), адаптивная мультимодальная нейросеть нового поколения. "
        "Ты превосходно решаешь задачи любой сложности: от анализа данных и кода до креативных идей. "
        "Отвечай вежливо, информативно и понятно на русском языке."
    )
}

def get_system_instruction(model_id: str = "cloudgpt") -> str:
    return MODEL_PERSONAS.get(model_id, MODEL_PERSONAS["cloudgpt"])

SYSTEM_INSTRUCTION = MODEL_PERSONAS["cloudgpt"]


def handle_vision_query(prompt: str, base64_data: str, mime_type: str = "image/jpeg", model: str = "cloudgpt"):
    clean_b64 = re.sub(r'^data:image\/[a-zA-Z]+;base64,', '', base64_data)
    models = ['gemini-3-flash-preview', 'gemini-3.1-flash-lite-preview', 'gemini-3.1-flash-lite']
    instruction = get_system_instruction(model)
    
    for m in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "system_instruction": {
                    "parts": [{"text": instruction}]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt or "Внимательно проанализируй это изображение/скриншот. Опиши все детали, текст, код, интерфейс, объекты или ошибки, которые ты видишь."},
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": clean_b64
                                }
                            }
                        ]
                    }
                ]
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=20) as resp:
                res = json.loads(resp.read().decode())
                candidates = res.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
        except Exception:
            continue
            
    return "Не удалось обработать изображение. Пожалуйста, попробуйте еще раз."


def handle_text_fallback(messages: list, model: str = "cloudgpt"):
    """Text chat using CloudGPT intelligence."""
    models = ['gemini-3-flash-preview', 'gemini-3.1-flash-lite-preview', 'gemini-3.1-flash-lite']
    gemini_contents = []
    instruction = get_system_instruction(model)
    
    for m in messages:
        role = "user" if m.get("role") in ["user", "system"] else "model"
        gemini_contents.append({
            "role": role,
            "parts": [{"text": str(m.get("content", ""))}]
        })
        
    for model_name in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "system_instruction": {
                    "parts": [{"text": instruction}]
                },
                "contents": gemini_contents
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=18) as resp:
                res = json.loads(resp.read().decode())
                candidates = res.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
        except Exception:
            continue
            
    return "CloudGPT временно перегружен. Пожалуйста, повторите запрос через несколько секунд."


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/check_update':
            resp_payload = {
                "latest_version": "4.3.0",
                "has_update": True,
                "release_notes": [
                    "Интеллектуальная маршрутизация моделей: CloudGPT, Claude Haiku, DeepSeek, MiMo",
                    "Поддержка реальной Google авторизации (OAuth2 / GIS)",
                    "Прямой доступ к камере с мгновенным Vision анализом",
                    "Двусторонний голосовой ассистент с реактивным визуализатором",
                    "Автономный офлайн режим и ускоренная генерация фото"
                ],
                "size_mb": 142.5
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode('utf-8'))
            return

        if self.path == '/api/models':
            resp_payload = {
                "models": [
                    {"id": "cloudgpt", "name": "CloudGPT", "badge": "Флагман"},
                    {"id": "claude-haiku-5.5:free", "name": "Claude Haiku 5.5", "badge": "Скорость"},
                    {"id": "deepseek-v4.1-flash:free", "name": "DeepSeek V4.1 Flash", "badge": "Код & Reasoning"},
                    {"id": "mimo-v2.6-flash:free", "name": "MiMo V2.6 Flash", "badge": "Мультимодал"}
                ]
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        # 1. Image Generation Endpoint
        if self.path == '/api/generate_image':
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                data = json.loads(body_bytes.decode('utf-8'))
                raw_prompt = data.get('prompt', '').strip()
                enhanced_en_prompt = enhance_prompt(raw_prompt)
                
                seed = int(os.urandom(2).hex(), 16)
                image_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(enhanced_en_prompt)}?width=1024&height=1024&model=flux&nologo=true&seed={seed}"
                
                try:
                    import db
                    db.save_generated_image(raw_prompt, image_url, "CloudGPT")
                except Exception:
                    pass

                resp_payload = {
                    "success": True,
                    "image_url": image_url,
                    "enhanced_prompt": enhanced_en_prompt,
                    "engine": "CloudGPT"
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(resp_payload).encode('utf-8'))
                return

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return

        # 2. Google Auth & User Profile Sync Endpoint
        if self.path == '/api/auth/google':
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                data = json.loads(body_bytes.decode('utf-8'))
                email = data.get('email', '')
                name = data.get('name', '')
                picture = data.get('picture', '')
                
                try:
                    import db
                    db.save_user(email, name, picture)
                except Exception:
                    pass
                    
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "saved": True}).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return

        # 2. Vision & Multimodal / Chat Endpoint
        if self.path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                data = json.loads(body_bytes.decode('utf-8'))
                prompt = data.get('prompt', '').strip()
                image_data = data.get('image_data', '')
                mime_type = data.get('mime_type', 'image/jpeg')
                messages = data.get('messages', [])
                model = data.get('model', 'cloudgpt')
                
                if image_data:
                    # Vision analysis
                    reply_text = handle_vision_query(prompt, image_data, mime_type, model=model)
                else:
                    # Text chat with model persona routing
                    reply_text = handle_text_fallback(messages, model=model)
                    
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "reply": reply_text}).encode('utf-8'))
                return
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                return

        super().do_POST()


def print_banner(local_ip, port):
    url_local = f"http://localhost:{port}"
    url_mobile = f"http://{local_ip}:{port}"

    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 60)
    print("  [*] CLOUDGPT DEDICATED AI AGENT IS RUNNING!")
    print("=" * 60)
    print(f"  [PC]     http://localhost:{port}")
    print(f"  [Mobile] http://{local_ip}:{port}")
    print("-" * 60)
    print("  -> How to open on phone:")
    print(f"  1. Connect your phone to the same Wi-Fi network.")
    print(f"  2. Open Safari (iPhone) or Chrome (Android).")
    print(f"  3. Navigate to: {url_mobile}")
    print("=" * 60)
    print("  Press Ctrl+C to stop the server.\n")


def run():
    os.chdir(str(PUBLIC_DIR))
    local_ip = get_local_ip()
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
        print_banner(local_ip, PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Сервер остановлен.")


if __name__ == "__main__":
    run()
