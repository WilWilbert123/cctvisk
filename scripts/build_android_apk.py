#!/usr/bin/env python3
"""
Builds and signs a native Android APK (`cctv-assistant.apk`) for the
CCTV Network Discovery & Recovery Assistant using the installed Android SDK & JDK 17.

Features inside the APK:
1. Embeds the full compiled React/TypeScript frontend (`frontend/dist`) into `assets/`.
2. Includes a native Android top bar to switch between Host Server (`http://192.168.0.85:8000`)
   and Standalone On-Phone Mode.
3. Includes `@JavascriptInterface AndroidNativeScanner` performing real multi-threaded
   Java TCP/RTSP/HTTP local network discovery directly on the Android phone when the host PC is offline.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / "build_apk"
DIST_DIR = ROOT_DIR / "frontend" / "dist"
OUTPUT_APK = ROOT_DIR / "cctv-assistant.apk"

ANDROID_SDK = Path(os.environ.get("LOCALAPPDATA", "C:/Users/MIS-WILBERT/AppData/Local")) / "Android" / "Sdk"
BUILD_TOOLS = ANDROID_SDK / "build-tools" / "36.0.0"
PLATFORM_JAR = ANDROID_SDK / "platforms" / "android-37.0" / "android.jar"
JDK_HOME = Path("C:/Users/MIS-WILBERT/AppData/Local/Programs/Eclipse Adoptium/jdk-17.0.15.6-hotspot")

JAVAC = JDK_HOME / "bin" / "javac.exe"
KEYTOOL = JDK_HOME / "bin" / "keytool.exe"
AAPT2 = BUILD_TOOLS / "aapt2.exe"
D8 = BUILD_TOOLS / "d8.bat"
ZIPALIGN = BUILD_TOOLS / "zipalign.exe"
APKSIGNER = BUILD_TOOLS / "apksigner.bat"

MANIFEST_XML = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.cctv.discovery.assistant"
    android:versionCode="1"
    android:versionName="1.0.0">

    <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />

    <application
        android:label="CCTV Discovery Assistant"
        android:icon="@drawable/ic_launcher"
        android:usesCleartextTraffic="true"
        android:hardwareAccelerated="true"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

MAIN_ACTIVITY_JAVA = r"""package com.cctv.discovery.assistant;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.Socket;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.Enumeration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

public class MainActivity extends Activity {
    private WebView webView;
    private EditText hostInput;
    private final NativeScannerBridge scannerBridge = new NativeScannerBridge();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#020617"));

        // Top Connection Bar for switching between Host PC IP and On-Phone Standalone Scanner
        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setGravity(Gravity.CENTER_VERTICAL);
        topBar.setPadding(20, 14, 20, 14);
        topBar.setBackgroundColor(Color.parseColor("#0f172a"));

        TextView label = new TextView(this);
        label.setText("Host IP: ");
        label.setTextColor(Color.parseColor("#94a3b8"));
        label.setTextSize(12);
        topBar.addView(label);

        hostInput = new EditText(this);
        hostInput.setText("http://192.168.0.85:8000");
        hostInput.setTextColor(Color.WHITE);
        hostInput.setHintTextColor(Color.GRAY);
        hostInput.setTextSize(12);
        hostInput.setSingleLine(true);
        LinearLayout.LayoutParams inputParams = new LinearLayout.LayoutParams(
                0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f);
        inputParams.setMargins(8, 0, 8, 0);
        hostInput.setLayoutParams(inputParams);
        topBar.addView(hostInput);

        Button btnConnectHost = new Button(this);
        btnConnectHost.setText("Sync PC");
        btnConnectHost.setTextSize(11);
        btnConnectHost.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String url = hostInput.getText().toString().trim();
                if (!url.startsWith("http")) {
                    url = "http://" + url;
                }
                final String cleanUrl = url;
                webView.evaluateJavascript(
                    "window.localStorage.setItem('cctv_backend_host', '" + cleanUrl + "'); window.location.reload();",
                    null
                );
                Toast.makeText(MainActivity.this, "Synced to Host: " + cleanUrl, Toast.LENGTH_SHORT).show();
            }
        });
        topBar.addView(btnConnectHost);

        Button btnPhoneMode = new Button(this);
        btnPhoneMode.setText("Phone Scan");
        btnPhoneMode.setTextSize(11);
        btnPhoneMode.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                webView.evaluateJavascript(
                    "window.localStorage.setItem('cctv_backend_host', 'http://127.0.0.1:9'); window.location.reload();",
                    null
                );
                Toast.makeText(MainActivity.this, "Switched to Standalone On-Phone Wi-Fi Scanner", Toast.LENGTH_SHORT).show();
            }
        });
        topBar.addView(btnPhoneMode);

        root.addView(topBar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(false);

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());
        webView.addJavascriptInterface(scannerBridge, "AndroidNativeScanner");

        root.addView(webView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1.0f));

        setContentView(root);
        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    public class NativeScannerBridge {
        private final Map<Integer, String> devicesJsonMap = new ConcurrentHashMap<>();
        private final Map<Integer, String> camerasJsonMap = new ConcurrentHashMap<>();
        private final AtomicBoolean isScanning = new AtomicBoolean(false);
        private final AtomicInteger scanProgress = new AtomicInteger(0);
        private volatile String scanStage = "idle";
        private volatile String scanMessage = "Ready to scan phone Wi-Fi network";
        private final AtomicInteger devicesFound = new AtomicInteger(0);
        private final AtomicInteger camerasFound = new AtomicInteger(0);

        private String detectPhoneIp() {
            try {
                Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
                for (NetworkInterface nif : Collections.list(interfaces)) {
                    if (nif.isLoopback() || !nif.isUp()) continue;
                    for (InetAddress addr : Collections.list(nif.getInetAddresses())) {
                        if (addr instanceof Inet4Address && !addr.isLoopbackAddress()) {
                            String ip = addr.getHostAddress();
                            if (ip != null && (ip.startsWith("192.168.") || ip.startsWith("10.") || ip.startsWith("172."))) {
                                return ip;
                            }
                        }
                    }
                }
            } catch (Exception ignored) {}
            return "192.168.0.100";
        }

        private String getSubnetPrefix(String ip) {
            int lastDot = ip.lastIndexOf('.');
            return lastDot > 0 ? ip.substring(0, lastDot) : "192.168.0";
        }

        private void startPhoneWifiScan(final String subnetCidr) {
            if (isScanning.getAndSet(true)) return;
            scanProgress.set(5);
            scanStage = "scanning";
            scanMessage = "Scanning Wi-Fi from Android phone...";
            devicesFound.set(0);
            camerasFound.set(0);
            devicesJsonMap.clear();
            camerasJsonMap.clear();

            new Thread(new Runnable() {
                @Override
                public void run() {
                    try {
                        String phoneIp = detectPhoneIp();
                        String prefix = getSubnetPrefix(phoneIp);
                        if (subnetCidr != null && subnetCidr.contains(".")) {
                            int slash = subnetCidr.indexOf('/');
                            String base = slash > 0 ? subnetCidr.substring(0, slash) : subnetCidr;
                            prefix = getSubnetPrefix(base);
                        }
                        final String targetPrefix = prefix;
                        final int[] probePorts = new int[]{80, 443, 445, 554, 8000, 8080, 37777, 34567, 9100, 53};
                        ExecutorService pool = Executors.newFixedThreadPool(48);
                        final AtomicInteger completed = new AtomicInteger(0);
                        final AtomicInteger idSeq = new AtomicInteger(1);

                        for (int host = 1; host <= 254; host++) {
                            final int h = host;
                            final String ip = targetPrefix + "." + h;
                            pool.submit(new Runnable() {
                                @Override
                                public void run() {
                                    try {
                                        List<Integer> openPorts = new ArrayList<>();
                                        long bestLatency = -1;
                                        boolean alive = false;

                                        for (int p : probePorts) {
                                            long t0 = System.currentTimeMillis();
                                            Socket s = new Socket();
                                            try {
                                                s.connect(new InetSocketAddress(ip, p), 280);
                                                long dt = System.currentTimeMillis() - t0;
                                                openPorts.add(p);
                                                alive = true;
                                                if (bestLatency < 0 || dt < bestLatency) bestLatency = dt;
                                            } catch (Exception e) {
                                                String msg = e.getMessage();
                                                if (msg != null && msg.toLowerCase(Locale.US).contains("refused")) {
                                                    long dt = System.currentTimeMillis() - t0;
                                                    alive = true;
                                                    if (bestLatency < 0 || dt < bestLatency) bestLatency = dt;
                                                }
                                            } finally {
                                                try { s.close(); } catch (Exception ignored) {}
                                            }
                                        }

                                        if (!alive) {
                                            try {
                                                long t0 = System.currentTimeMillis();
                                                if (InetAddress.getByName(ip).isReachable(300)) {
                                                    alive = true;
                                                    bestLatency = System.currentTimeMillis() - t0;
                                                }
                                            } catch (Exception ignored) {}
                                        }

                                        if (alive) {
                                            int devId = idSeq.getAndIncrement();
                                            boolean isCamera = openPorts.contains(554) || openPorts.contains(8000) || openPorts.contains(37777) || openPorts.contains(34567);
                                            String category = "UNKNOWN";
                                            String model = "LAN Network Node";
                                            String manufacturer = "Discovered via Android Wi-Fi";
                                            String confidence = "MEDIUM";

                                            if (isCamera) {
                                                category = "CAMERA";
                                                model = "IP CCTV Camera / NVR";
                                                manufacturer = openPorts.contains(8000) ? "Hikvision / ONVIF" : (openPorts.contains(37777) ? "Dahua / ONVIF" : "RTSP Camera");
                                                confidence = "HIGH";
                                            } else if (h == 1 || openPorts.contains(53)) {
                                                category = "ROUTER";
                                                model = "Wi-Fi Gateway / Router";
                                                confidence = "HIGH";
                                            } else if (openPorts.contains(9100)) {
                                                category = "PRINTER";
                                                model = "Network Printer";
                                            } else if (openPorts.contains(445)) {
                                                category = "COMPUTER";
                                                model = "Windows / SMB Workstation";
                                            }

                                            StringBuilder portsArr = new StringBuilder("[");
                                            for (int i = 0; i < openPorts.size(); i++) {
                                                if (i > 0) portsArr.append(",");
                                                portsArr.append(openPorts.get(i));
                                            }
                                            portsArr.append("]");

                                            String nowIso = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).format(new Date());
                                            String devJson = "{"
                                                + "\"id\":" + devId + ","
                                                + "\"ip_address\":\"" + ip + "\","
                                                + "\"mac_address\":null,"
                                                + "\"hostname\":\"" + ip + "\","
                                                + "\"label\":\"" + model + " (" + ip + ")\","
                                                + "\"manufacturer\":\"" + manufacturer + "\","
                                                + "\"model\":\"" + model + "\","
                                                + "\"category\":\"" + category + "\","
                                                + "\"confidence\":\"" + confidence + "\","
                                                + "\"is_online\":true,"
                                                + "\"latency_ms\":" + (bestLatency >= 0 ? bestLatency : 12) + ","
                                                + "\"open_ports\":" + portsArr.toString() + ","
                                                + "\"discovery_methods\":[\"ANDROID_TCP\",\"WIFI\"],"
                                                + "\"classification_evidence\":[\"Discovered directly by Android phone on " + targetPrefix + ".0/24\"],"
                                                + "\"last_seen\":\"" + nowIso + "\""
                                                + "}";
                                            devicesJsonMap.put(devId, devJson);
                                            devicesFound.incrementAndGet();

                                            if (isCamera) {
                                                String camJson = "{"
                                                    + "\"id\":" + devId + ","
                                                    + "\"device_id\":" + devId + ","
                                                    + "\"ip_address\":\"" + ip + "\","
                                                    + "\"label\":\"Camera " + ip + "\","
                                                    + "\"manufacturer\":\"" + manufacturer + "\","
                                                    + "\"model\":\"" + model + "\","
                                                    + "\"rtsp_port\":554,"
                                                    + "\"http_port\":80,"
                                                    + "\"onvif_port\":80,"
                                                    + "\"is_online\":true,"
                                                    + "\"onvif_supported\":true,"
                                                    + "\"rtsp_supported\":true"
                                                    + "}";
                                                camerasJsonMap.put(devId, camJson);
                                                camerasFound.incrementAndGet();
                                            }
                                        }
                                    } finally {
                                        int done = completed.incrementAndGet();
                                        scanProgress.set(Math.min(99, 5 + (done * 94 / 254)));
                                        scanMessage = "Scanned " + done + "/254 hosts (" + devicesFound.get() + " found)...";
                                    }
                                }
                            });
                        }
                        pool.shutdown();
                        pool.awaitTermination(25, TimeUnit.SECONDS);
                    } catch (Exception ignored) {
                    } finally {
                        scanProgress.set(100);
                        scanStage = "completed";
                        scanMessage = "Android Wi-Fi scan complete (" + devicesFound.get() + " devices, " + camerasFound.get() + " cameras)";
                        isScanning.set(false);
                    }
                }
            }).start();
        }

        @JavascriptInterface
        public String handleApiRequest(String method, String endpoint, String body) {
            String phoneIp = detectPhoneIp();
            String subnetCidr = getSubnetPrefix(phoneIp) + ".0/24";
            String gatewayIp = getSubnetPrefix(phoneIp) + ".1";
            String nowIso = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).format(new Date());

            if (endpoint.contains("/network/info") || endpoint.contains("/network/interfaces")) {
                return "{\"interface_name\":\"wlan0\",\"ip_address\":\"" + phoneIp + "\","
                     + "\"subnet_cidr\":\"" + subnetCidr + "\",\"netmask\":\"255.255.255.0\","
                     + "\"gateway\":\"" + gatewayIp + "\",\"is_connected\":true,\"connection_type\":\"Wi-Fi (Android Native)\"}";
            }
            if (endpoint.contains("/network/scan") && "POST".equalsIgnoreCase(method)) {
                startPhoneWifiScan(subnetCidr);
                return "{\"id\":1,\"subnet_cidr\":\"" + subnetCidr + "\",\"status\":\"running\",\"progress\":5,\"stage\":\"scanning\"}";
            }
            if (endpoint.contains("/network/scan/status")) {
                return "{\"is_running\":" + isScanning.get() + ",\"progress\":" + scanProgress.get()
                     + ",\"stage\":\"" + scanStage + "\",\"message\":\"" + scanMessage + "\","
                     + "\"devices_found\":" + devicesFound.get() + ",\"cameras_found\":" + camerasFound.get() + "}";
            }
            if (endpoint.startsWith("/devices")) {
                StringBuilder items = new StringBuilder("[");
                boolean first = true;
                for (String d : devicesJsonMap.values()) {
                    if (!first) items.append(",");
                    items.append(d);
                    first = false;
                }
                items.append("]");
                return "{\"items\":" + items.toString() + ",\"total\":" + devicesJsonMap.size() + ",\"page\":1,\"page_size\":100}";
            }
            if (endpoint.startsWith("/cameras")) {
                StringBuilder items = new StringBuilder("[");
                boolean first = true;
                for (String c : camerasJsonMap.values()) {
                    if (!first) items.append(",");
                    items.append(c);
                    first = false;
                }
                items.append("]");
                return "{\"items\":" + items.toString() + ",\"total\":" + camerasJsonMap.size() + "}";
            }
            if (endpoint.contains("/system/dashboard")) {
                StringBuilder rec = new StringBuilder("[");
                boolean first = true;
                int count = 0;
                for (String d : devicesJsonMap.values()) {
                    if (count++ >= 8) break;
                    if (!first) rec.append(",");
                    rec.append(d);
                    first = false;
                }
                rec.append("]");
                return "{"
                    + "\"network\":{\"interface_name\":\"wlan0\",\"ip_address\":\"" + phoneIp + "\",\"subnet_cidr\":\"" + subnetCidr + "\",\"netmask\":\"255.255.255.0\",\"gateway\":\"" + gatewayIp + "\",\"mac_address\":null,\"is_connected\":true,\"connection_type\":\"Android Wi-Fi\",\"ssid\":null},"
                    + "\"counts\":{\"total_devices\":" + devicesJsonMap.size() + ",\"online_devices\":" + devicesJsonMap.size() + ",\"offline_devices\":0,\"cameras_count\":" + camerasJsonMap.size() + ",\"nvr_dvr_count\":0,\"unknown_devices\":0,\"monitored_devices\":" + devicesJsonMap.size() + "},"
                    + "\"latest_scan\":{\"id\":1,\"subnet_cidr\":\"" + subnetCidr + "\",\"status\":\"" + scanStage + "\",\"progress\":" + scanProgress.get() + ",\"devices_found\":" + devicesFound.get() + ",\"cameras_found\":" + camerasFound.get() + ",\"started_at\":\"" + nowIso + "\"},"
                    + "\"recent_devices\":" + rec.toString() + ","
                    + "\"monitoring_activity\":[],"
                    + "\"status_distribution\":[{\"name\":\"Online\",\"value\":" + devicesJsonMap.size() + ",\"category\":\"status\"}],"
                    + "\"recent_events\":[]"
                    + "}";
            }
            if (endpoint.contains("/monitoring/status")) {
                return "{\"is_running\":true,\"interval_seconds\":60,\"timeout_ms\":1000,\"total_monitored\":" + devicesJsonMap.size() + ",\"online_count\":" + devicesJsonMap.size() + ",\"offline_count\":0,\"devices\":[],\"availability_series\":[],\"recent_alerts\":[]}";
            }
            return "{\"items\":[],\"total\":0}";
        }
    }
}
"""


def create_launcher_icon(icon_path: Path) -> None:
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (192, 192), (37, 99, 235, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(24, 24), (168, 168)], outline=(255, 255, 255, 255), width=8)
    draw.ellipse([(68, 68), (124, 124)], fill=(255, 255, 255, 255))
    img.save(icon_path, format="PNG")


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    res = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(
            f"Command failed ({res.returncode}): {' '.join(cmd)}\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )


def main() -> None:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    manifest_file = BUILD_DIR / "AndroidManifest.xml"
    manifest_file.write_text(MANIFEST_XML, encoding="utf-8")

    res_dir = BUILD_DIR / "res"
    create_launcher_icon(res_dir / "drawable" / "ic_launcher.png")

    java_file = BUILD_DIR / "src" / "com" / "cctv" / "discovery" / "assistant" / "MainActivity.java"
    java_file.parent.mkdir(parents=True, exist_ok=True)
    java_file.write_text(MAIN_ACTIVITY_JAVA, encoding="utf-8")

    # 1. Compile resources with aapt2
    compiled_res_zip = BUILD_DIR / "compiled_res.zip"
    run_cmd([str(AAPT2), "compile", "--dir", str(res_dir), "-o", str(compiled_res_zip)])

    # 2. Link resources & manifest with aapt2 and generate R.java
    gen_dir = BUILD_DIR / "gen"
    gen_dir.mkdir(parents=True, exist_ok=True)
    unsigned_apk = BUILD_DIR / "unaligned.apk"
    run_cmd(
        [
            str(AAPT2),
            "link",
            "-o",
            str(unsigned_apk),
            "-I",
            str(PLATFORM_JAR),
            "--manifest",
            str(manifest_file),
            "--java",
            str(gen_dir),
            str(compiled_res_zip),
        ]
    )

    # 3. Compile Java sources with javac (targeting Java 8 bytecode for d8)
    classes_dir = BUILD_DIR / "classes"
    classes_dir.mkdir(parents=True, exist_ok=True)
    r_java = gen_dir / "com" / "cctv" / "discovery" / "assistant" / "R.java"
    run_cmd(
        [
            str(JAVAC),
            "-source",
            "1.8",
            "-target",
            "1.8",
            "-bootclasspath",
            str(PLATFORM_JAR),
            "-classpath",
            str(PLATFORM_JAR),
            "-d",
            str(classes_dir),
            str(r_java),
            str(java_file),
        ]
    )

    # 4. Convert .class files to classes.dex using d8
    class_files = [str(p) for p in classes_dir.rglob("*.class")]
    env = os.environ.copy()
    env["JAVA_HOME"] = str(JDK_HOME)
    env["PATH"] = f"{JDK_HOME / 'bin'};{env.get('PATH', '')}"
    res = subprocess.run(
        [str(D8), "--lib", str(PLATFORM_JAR), "--output", str(BUILD_DIR), *class_files],
        env=env,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"d8 failed: {res.stderr}\n{res.stdout}")

    # 5. Add classes.dex and frontend/dist/* (as assets/*) into unsigned_apk
    with zipfile.ZipFile(unsigned_apk, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(BUILD_DIR / "classes.dex", "classes.dex")
        for asset_file in DIST_DIR.rglob("*"):
            if asset_file.is_file():
                rel = asset_file.relative_to(DIST_DIR).as_posix()
                zf.write(asset_file, f"assets/{rel}")

    # 6. Align APK with zipalign
    aligned_apk = BUILD_DIR / "aligned.apk"
    run_cmd([str(ZIPALIGN), "-f", "-p", "4", str(unsigned_apk), str(aligned_apk)])

    # 7. Generate signing keystore and sign APK with apksigner (v1 + v2 signatures)
    keystore = BUILD_DIR / "debug.keystore"
    run_cmd(
        [
            str(KEYTOOL),
            "-genkeypair",
            "-v",
            "-keystore",
            str(keystore),
            "-storepass",
            "android",
            "-alias",
            "androiddebugkey",
            "-keypass",
            "android",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-dname",
            "CN=Android Debug,O=Android,C=US",
        ]
    )

    res_sign = subprocess.run(
        [
            str(APKSIGNER),
            "sign",
            "--ks",
            str(keystore),
            "--ks-pass",
            "pass:android",
            "--key-pass",
            "pass:android",
            "--out",
            str(OUTPUT_APK),
            str(aligned_apk),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if res_sign.returncode != 0:
        raise RuntimeError(f"apksigner failed: {res_sign.stderr}\n{res_sign.stdout}")

    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    print(f"Successfully built signed Android APK: {OUTPUT_APK} ({OUTPUT_APK.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

