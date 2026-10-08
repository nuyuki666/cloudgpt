# train_agent.py - CloudGPT Autonomous Mega-Training & Deep Distillation Engine
import json
import os
import sys
import time
import urllib.request
import threading
from pathlib import Path

PUBLIC_DIR = Path(__file__).resolve().parent / "public"
KNOWLEDGE_FILE = PUBLIC_DIR / "knowledge_base.json"

import base64

_d = lambda s: base64.b64decode(s).decode('utf-8')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or _d("QVEuQWI4Uk42SkVtTW9UNWtqdzhjQUhfQ0NBMi16TDBsOFBMc2dRYS1lNWhPXzllZ2VmSFE=")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY") or _d("c2stb3ItdjEtMzQwY2EzM2Q5MTI1NDQ4MmJiNGZhMjhjMjgwNzAyZTg0OTkyMmU2NGM3Y2EzYjZkMDhhNTE2MmVkMDczNWFhYw==")

EXPANDED_CURRICULUM = [
    {
        "category": "Game Memory & AOB Scanning",
        "topic": "Multi-threaded SIMD AVX2 AOB Pattern Scanner in C++",
        "prompt": "Write a high-performance C++20 x64 AVX2 / SSE pattern scanner for scanning gigabytes of process memory in parallel with chunking and wildcard masks '?'."
    },
    {
        "category": "Manual Map Injection",
        "topic": "Stealth Manual Map DLL Injector with Exception Directory and TLS Support",
        "prompt": "Write a full C++ Manual Map injector from scratch that handles IMAGE_DIRECTORY_ENTRY_EXCEPTION, TLS Callbacks, Base Relocations, and IAT resolution."
    },
    {
        "category": "Kernel & Driver Communication",
        "topic": "Kernel-mode Driver IOCTL Communication for Physical Memory Read/Write in C",
        "prompt": "Write a complete Windows KMDF driver and User-mode Client using DeviceIoControl and MmCopyVirtualMemory to read/write target process memory safely."
    },
    {
        "category": "VMT & Mid-Function Hooking",
        "topic": "Hardware Breakpoint (DR0-DR7) and Mid-Function Trampoline Hook Engine in C++",
        "prompt": "Implement a C++ library for setting Hardware Breakpoints via GetThreadContext / SetThreadContext and Vectored Exception Handling (VEH) for hookless memory modification."
    },
    {
        "category": "Game Math & 3D Projections",
        "topic": "Comprehensive 3D Vector, Quaternions, and WorldToScreen Projection Matrix Class",
        "prompt": "Write an enterprise-grade 3D Math class in C++ (Vector3, Vector4, Matrix4x4, Quaternion) with WorldToScreen, Angle Calculation (Pitch/Yaw), and Smooth Aimbot FOV delta algorithms."
    },
    {
        "category": "DirectX 11/12 & ImGui",
        "topic": "DirectX 11 & DirectX 12 IDXGISwapChain Present & ResizeBuffers Hook with ImGui",
        "prompt": "Write complete C++ code to hook IDXGISwapChain::Present and ResizeBuffers in DirectX 11 / 12 for rendering ImGui in fullscreen borderless games."
    },
    {
        "category": "Reverse Engineering & Anti-Anti-Cheat",
        "topic": "Bypassing PEB Debugger Flags, ThreadHideFromDebugger, and Page Protection CRC Checks",
        "prompt": "Explain and provide C++ code for stealth memory patching bypassing page checksum CRC scans using Page Guards / PAGE_NOACCESS with VEH page fault handler."
    },
    {
        "category": "Low-Level Syscalls & Shellcode",
        "topic": "Direct NT Syscalls with Hell's Gate and Halos Gate in C++ and Assembly",
        "prompt": "Write a complete implementation of Hell's Gate and Halo's Gate dynamic SSN syscall resolution in x64 MASM assembly and C++ to bypass EDR/AV hooks."
    },
    {
        "category": "Computer Vision & Visual Recognition",
        "topic": "Real-time TensorRT YOLOv8 Screen Detection and Visual Recognition Engine in C++",
        "prompt": "Write a high-performance C++ module for capturing desktop/game screen frames via Windows Desktop Duplication API (DXGI) and running TensorRT YOLOv8 inference for bounding box detection."
    },
    {
        "category": "Multimodal Deep Learning",
        "topic": "Vision Transformer (ViT) with Patch Embeddings and Multi-Head Self-Attention from Scratch",
        "prompt": "Implement a Vision Transformer (ViT) in PyTorch from scratch, explaining patch projection, [CLS] token, learnable positional embeddings, and Multi-Head Attention blocks with mathematical formulas."
    },
    {
        "category": "Deobfuscation & Virtualization",
        "topic": "Virtual Machine Architecture Obfuscation Analysis and Control Flow Flattening Deobfuscation",
        "prompt": "Explain how VM-based packers (VMProtect, Themida) virtualize x86 instructions into bytecode handler dispatch loops, and how to write an automated symbolic execution deobfuscator using Triton or Miasm."
    },
    {
        "category": "Distributed Systems & Highload",
        "topic": "High-Throughput Distributed Microservice in Go with pgx, Redis, Kafka, and OpenTelemetry",
        "prompt": "Write a production-grade Go microservice with clean architecture, PostgreSQL connection pool, Redis cache-aside, Kafka event publisher, and Prometheus metrics."
    }
]


def load_knowledge():
    if KNOWLEDGE_FILE.exists():
        try:
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_knowledge(kb):
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def distill_topic(item):
    prompt = f"Ты — главный архитектор CloudGPT. Напиши исчерпывающий, глубокий инженерный модуль с полным рабочим кодом, комментариями и архитектурой по теме: «{item['topic']}».\nЗадача: {item['prompt']}"

    # Try Gemini 3 Flash first
    gemini_models = ['gemini-3-flash-preview', 'gemini-3.1-flash-lite-preview', 'gemini-3.1-flash-lite']
    for m in gemini_models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ]
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=25) as resp:
                res = json.loads(resp.read().decode())
                candidates = res.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
        except Exception:
            continue

    return None


def run_training_cycle():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 70)
    print("  [*] CLOUDGPT AUTONOMOUS VISION & REVERSE ENGINEERING TRAINING")
    print("=" * 70)
    
    kb = load_knowledge()
    existing_topics = {k.get("topic") for k in kb}
    print(f"[*] Current Knowledge Store: {len(kb)} modules.")
    
    for idx, item in enumerate(EXPANDED_CURRICULUM, 1):
        if item["topic"] in existing_topics:
            print(f"[{idx}/{len(EXPANDED_CURRICULUM)}] [CACHED] {item['topic']}")
            continue
            
        print(f"\n[{idx}/{len(EXPANDED_CURRICULUM)}] Training topic: {item['topic']}...")
        response = distill_topic(item)
        
        if response and len(response) > 200:
            kb.append({
                "category": item["category"],
                "topic": item["topic"],
                "response": response,
                "timestamp": time.time()
            })
            save_knowledge(kb)
            print(f"   [SUCCESS] Distilled {len(response)} chars into CloudGPT store!")
        else:
            print(f"   [WARN] Skipping topic due to temporary API limit.")
            
        time.sleep(1)

    print("\n" + "=" * 70)
    print(f"  [SUCCESS] TRAINING ROUND FINISHED! Total Knowledge Modules: {len(kb)}")
    print("=" * 70)


if __name__ == "__main__":
    run_training_cycle()
