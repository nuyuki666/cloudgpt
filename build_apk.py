# build_apk.py
# Automated Standalone Android APK Builder for CloudGPT Mobile (with full v1/v2/v3 signing & zipalign)
import os
import sys
import subprocess
import zipfile
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BUILD_DIR = BASE_DIR / "apk_build"
TOOLS_DIR = BASE_DIR / "apk_tools"
PUBLIC_DIR = BASE_DIR / "public"

JAVA_BIN = Path("C:/Program Files/Java/jdk-25.0.4/bin")
JAVAC = str(JAVA_BIN / "javac.exe") if (JAVA_BIN / "javac.exe").exists() else "javac"
JAVA = str(JAVA_BIN / "java.exe") if (JAVA_BIN / "java.exe").exists() else "java"

AAPT2 = str(TOOLS_DIR / "aapt2.exe")
R8_JAR = str(TOOLS_DIR / "r8.jar")
ANDROID_JAR = str(TOOLS_DIR / "android.jar")
UBER_SIGNER = str(TOOLS_DIR / "uber-apk-signer.jar")

KEYSTORE_PATH = BASE_DIR / "cloudgpt.keystore"
OUTPUT_APK = BASE_DIR / "CloudGPT-Mobile.apk"


def log(msg):
    print(f"[APK BUILDER] {msg}")


def generate_app_icon(dest_path, size=(192, 192)):
    """Generate high quality PNG app icon from user images.png."""
    icon_source = BASE_DIR / "images.png"
    if icon_source.exists():
        try:
            from PIL import Image
            img = Image.open(icon_source).convert('RGBA')
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            img.resize(size, Image.Resampling.LANCZOS).save(dest_path, "PNG")
            return
        except Exception:
            pass
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGBA', size, color=(13, 15, 32, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse((4, 4, size[0] - 4, size[1] - 4), fill=(79, 91, 255, 255))
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest_path, "PNG")
    except Exception:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        raw_png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360606060000000050001a5f645400000000049454e44ae426082")
        with open(dest_path, "wb") as f:
            f.write(raw_png)


def setup_project_structure():
    log("Setting up Android project files...")
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # 1. AndroidManifest.xml
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.cloudgpt.app"
    android:versionCode="1"
    android:versionName="1.0">

    <uses-sdk android:minSdkVersion="21" android:targetSdkVersion="33" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />

    <application
        android:label="@string/app_name"
        android:icon="@mipmap/ic_launcher"
        android:allowBackup="true"
        android:hardwareAccelerated="true"
        android:usesCleartextTraffic="true"
        android:theme="@android:style/Theme.NoTitleBar">
        
        <activity
            android:name="com.cloudgpt.app.MainActivity"
            android:label="@string/app_name"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:windowSoftInputMode="adjustResize"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
    with open(BUILD_DIR / "AndroidManifest.xml", "w", encoding="utf-8") as f:
        f.write(manifest_content)

    # 2. Resources (res/values/strings.xml, icons)
    values_dir = BUILD_DIR / "res" / "values"
    values_dir.mkdir(parents=True, exist_ok=True)
    with open(values_dir / "strings.xml", "w", encoding="utf-8") as f:
        f.write("""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">CloudGPT</string>
</resources>
""")

    generate_app_icon(BUILD_DIR / "res" / "mipmap-mdpi" / "ic_launcher.png", (48, 48))
    generate_app_icon(BUILD_DIR / "res" / "mipmap-hdpi" / "ic_launcher.png", (72, 72))
    generate_app_icon(BUILD_DIR / "res" / "mipmap-xhdpi" / "ic_launcher.png", (96, 96))
    generate_app_icon(BUILD_DIR / "res" / "mipmap-xxhdpi" / "ic_launcher.png", (144, 144))
    generate_app_icon(BUILD_DIR / "res" / "mipmap-xxxhdpi" / "ic_launcher.png", (192, 192))

    # 3. Java Source
    src_dir = BUILD_DIR / "src" / "com" / "cloudgpt" / "app"
    src_dir.mkdir(parents=True, exist_ok=True)
    java_code = """package com.cloudgpt.app;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.content.Intent;
import android.net.Uri;
import android.view.Window;
import android.view.WindowManager;
import android.os.Build;
import android.graphics.Color;
import android.content.pm.PackageManager;
import android.Manifest;

public class MainActivity extends Activity {
    private WebView mWebView;
    private ValueCallback<Uri[]> mFilePathCallback;
    private final static int FILECHOOSER_RESULTCODE = 1;
    private final static int PERMISSION_REQUEST_CODE = 101;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Window window = getWindow();
            window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
            window.setStatusBarColor(Color.parseColor("#0D0F20"));
        }

        // Request real runtime camera & microphone permissions
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            String[] permissions = {
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO,
                Manifest.permission.MODIFY_AUDIO_SETTINGS
            };
            boolean needReq = false;
            for (String p : permissions) {
                if (checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) {
                    needReq = true;
                    break;
                }
            }
            if (needReq) {
                requestPermissions(permissions, PERMISSION_REQUEST_CODE);
            }
        }

        mWebView = new WebView(this);
        setContentView(mWebView);

        WebSettings settings = mWebView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(true);
        settings.setSupportMultipleWindows(true);

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        // Clean user agent for Google auth
        try {
            String defaultUA = settings.getUserAgentString();
            if (defaultUA != null) {
                settings.setUserAgentString(defaultUA.replace("; wv", ""));
            }
        } catch (Exception e) {}

        mWebView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return false;
            }
        });

        mWebView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                MainActivity.this.runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        try {
                            request.grant(request.getResources());
                        } catch (Exception e) {
                            try {
                                request.grant(new String[]{
                                    PermissionRequest.RESOURCE_VIDEO_CAPTURE,
                                    PermissionRequest.RESOURCE_AUDIO_CAPTURE
                                });
                            } catch (Exception ex) {}
                        }
                    }
                });
            }

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (mFilePathCallback != null) {
                    mFilePathCallback.onReceiveValue(null);
                }
                mFilePathCallback = filePathCallback;

                try {
                    Intent takePictureIntent = new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
                    Intent contentSelectionIntent = new Intent(Intent.ACTION_GET_CONTENT);
                    contentSelectionIntent.addCategory(Intent.CATEGORY_OPENABLE);
                    contentSelectionIntent.setType("image/*");

                    Intent chooserIntent = Intent.createChooser(contentSelectionIntent, "Сделать фото или выбрать изображение");
                    chooserIntent.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[] { takePictureIntent });
                    startActivityForResult(chooserIntent, FILECHOOSER_RESULTCODE);
                } catch (Exception e) {
                    mFilePathCallback = null;
                    return false;
                }
                return true;
            }
        });

        mWebView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CODE) {
            if (mWebView != null) {
                mWebView.reload();
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILECHOOSER_RESULTCODE) {
            if (mFilePathCallback != null) {
                Uri[] results = null;
                if (resultCode == Activity.RESULT_OK && data != null) {
                    String dataString = data.getDataString();
                    if (dataString != null) {
                        results = new Uri[]{Uri.parse(dataString)};
                    } else if (data.getClipData() != null) {
                        int count = data.getClipData().getItemCount();
                        results = new Uri[count];
                        for (int i = 0; i < count; i++) {
                            results[i] = data.getClipData().getItemAt(i).getUri();
                        }
                    }
                }
                mFilePathCallback.onReceiveValue(results);
                mFilePathCallback = null;
            }
        } else {
            super.onActivityResult(requestCode, resultCode, data);
        }
    }

    @Override
    public void onBackPressed() {
        if (mWebView != null && mWebView.canGoBack()) {
            mWebView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
"""
    with open(src_dir / "MainActivity.java", "w", encoding="utf-8") as f:
        f.write(java_code)

    # 4. Web Assets in assets/
    assets_dir = BUILD_DIR / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    for f_name in ["index.html", "claudegpt-mobile.html", "favicon.png", "apple-touch-icon.png", "manifest.json", "knowledge_base.json"]:
        p = PUBLIC_DIR / f_name
        if p.exists():
            shutil.copy2(p, assets_dir / f_name)


def compile_resources():
    log("Compiling resources with aapt2...")
    res_zip = BUILD_DIR / "compiled_res.zip"
    cmd = [AAPT2, "compile", "--dir", str(BUILD_DIR / "res"), "-o", str(res_zip)]
    subprocess.run(cmd, check=True)

    log("Linking resources and packaging assets...")
    unaligned_apk = BUILD_DIR / "unaligned.apk"
    cmd = [
        AAPT2, "link",
        "-I", ANDROID_JAR,
        "--manifest", str(BUILD_DIR / "AndroidManifest.xml"),
        "--min-sdk-version", "21",
        "--target-sdk-version", "33",
        "--version-code", "1",
        "--version-name", "1.0",
        "-o", str(unaligned_apk),
        str(res_zip),
        "-A", str(BUILD_DIR / "assets"),
        "--auto-add-overlay"
    ]
    subprocess.run(cmd, check=True)


def compile_java_and_dex():
    log("Compiling Java source code with javac...")
    bin_dir = BUILD_DIR / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    src_java = str(BUILD_DIR / "src" / "com" / "cloudgpt" / "app" / "MainActivity.java")
    cmd = [
        JAVAC,
        "-cp", ANDROID_JAR,
        "-d", str(bin_dir),
        "-source", "8",
        "-target", "8",
        src_java
    ]
    subprocess.run(cmd, check=True)

    log("Converting bytecode to classes.dex using D8/R8...")
    class_files = list(bin_dir.glob("**/*.class"))
    cmd = [
        JAVA,
        "-cp", R8_JAR,
        "com.android.tools.r8.D8",
        "--lib", ANDROID_JAR,
        "--min-api", "21",
        "--output", str(bin_dir)
    ] + [str(f) for f in class_files]
    subprocess.run(cmd, check=True)

    dex_file = bin_dir / "classes.dex"
    if not dex_file.exists():
        raise RuntimeError("classes.dex was not generated!")

    log("Injecting classes.dex into APK...")
    unaligned_apk = BUILD_DIR / "unaligned.apk"
    with zipfile.ZipFile(unaligned_apk, "a", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(dex_file, "classes.dex")


def sign_and_align_apk():
    log("Signing and zip-aligning APK (v1, v2, v3 schemes)...")
    unaligned_apk = BUILD_DIR / "unaligned.apk"
    
    # Run uber-apk-signer
    cmd = [
        JAVA, "-jar", UBER_SIGNER,
        "-a", str(unaligned_apk),
        "--overwrite",
        "--allowResign"
    ]
    subprocess.run(cmd, check=True)

    # Copy to output APK
    shutil.copy2(unaligned_apk, OUTPUT_APK)
    log(f"SUCCESS! Signed & zip-aligned APK generated at: {OUTPUT_APK} ({os.path.getsize(OUTPUT_APK)} bytes)")


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("=" * 60)
    print("  [*] BUILDING STANDALONE CLOUDGPT MOBILE APK")
    print("=" * 60)
    setup_project_structure()
    compile_resources()
    compile_java_and_dex()
    sign_and_align_apk()
    print("=" * 60)
    print("  [SUCCESS] APK BUILD COMPLETED SUCCESSFULLY!")
    print(f"  [APK] File: {OUTPUT_APK}")
    print(f"  [SIZE] Size: {os.path.getsize(OUTPUT_APK) / (1024*1024):.2f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
