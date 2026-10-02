"""
Rewardra.xyz - Vercel Serverless Backend
Uses user's IP via X-Forwarded-For
"""
import json
import time
import random
import re
import string
from http.server import BaseHTTPRequestHandler
from urllib.parse import quote

import requests

# ============================================================
# CONFIG
# ============================================================
BASE_URL = "https://rewardra.xyz"
SIGNUP_URL = f"{BASE_URL}/signup"
LOGIN_URL = f"{BASE_URL}/login"
OFFERS_URL = f"{BASE_URL}/user/offers"

PASSWORD = "7797212585@"
TARGET_OFFER_ID = 75926

TASK_BYPASS_URL = "https://narzo.fun/Adjust/?url={}&submit=SUBMIT"
TIMEOUT = 20

# ============================================================
# DEVICES (Random)
# ============================================================
DEVICES = [
    {"model": "CPH2729", "android": "16", "chrome": "153", "build": "BP2A.250605.015", "brand": "OPPO"},
    {"model": "SM-S928B", "android": "14", "chrome": "120", "build": "UP1A.231005.007", "brand": "samsung"},
    {"model": "Pixel 9 Pro", "android": "15", "chrome": "121", "build": "AP3A.241105.008", "brand": "Google"},
    {"model": "RMX3783", "android": "13", "chrome": "119", "build": "TP1A.220905.001", "brand": "realme"},
    {"model": "V2312", "android": "14", "chrome": "122", "build": "UP1A.231005.007", "brand": "vivo"},
    {"model": "SM-A155F", "android": "15", "chrome": "120", "build": "UP1A.231005.007", "brand": "samsung"},
    {"model": "M2101K6P", "android": "14", "chrome": "121", "build": "UKQ1.231003.002", "brand": "Xiaomi"},
    {"model": "OnePlus 12", "android": "15", "chrome": "122", "build": "UP1A.231005.007", "brand": "OnePlus"},
]

BROWSER_APPS = ["Aujbrqp/4.0", "SoulBrowser/1.0", "KiwiBrowser/1.0"]

APPS = [
    "com.mycompany.app.soulbrowser",
    "com.kiwibrowser.browser",
    "com.android.chrome",
]


# ============================================================
# HELPERS
# ============================================================
def random_device():
    return random.choice(DEVICES)


def random_ua(device):
    browser = random.choice(BROWSER_APPS)
    return f"Mozilla/5.0 (Linux; Android {device['android']}; {device['model']} Build/{device['build']}) AppleWebKit/537.36 (KHTML, like Gecko) {browser} Chrome/{device['chrome']}.0.0.0 Mobile Safari/537.36"


def random_xrw():
    return random.choice(APPS)


def random_email():
    prefixes = ["user", "acc", "mail", "id", "test", "new", "pro", "app", "web", "net", "go", "get"]
    prefixes2 = ["zx", "qw", "pl", "mk", "nb", "vc", "rt", "yu"]
    method = random.randint(1, 3)

    if method == 1:
        prefix = random.choice(prefixes)
        letters = ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 7)))
        digits = ''.join(random.choices(string.digits, k=random.randint(3, 5)))
        return f"{prefix}{letters}{digits}@gmail.com"
    elif method == 2:
        letters1 = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 8)))
        letters2 = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 5)))
        digits = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
        return f"{letters1}{letters2}{digits}@gmail.com"
    else:
        prefix = random.choice(prefixes2)
        letters = ''.join(random.choices(string.ascii_lowercase, k=random.randint(6, 9)))
        digits = ''.join(random.choices(string.digits, k=random.randint(3, 4)))
        return f"{prefix}{letters}{digits}@gmail.com"


def get_headers(referer=None, ajax=False, device=None, user_ip=None):
    if not device:
        device = random_device()

    headers = {
        "Host": "rewardra.xyz",
        "sec-ch-ua": f'"Android WebView";v="{device["chrome"]}", "Not_A Brand";v="8", "Chromium";v="{device["chrome"]}"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "upgrade-insecure-requests": "1",
        "user-agent": random_ua(device),
        "origin": BASE_URL,
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
        "sec-fetch-site": "same-origin",
        "x-requested-with": random_xrw(),
    }

    if ajax:
        headers["x-requested-with"] = "XMLHttpRequest"
        headers["accept"] = "application/json"
        headers["sec-fetch-mode"] = "cors"
        headers["sec-fetch-dest"] = "empty"
    else:
        headers["content-type"] = "application/x-www-form-urlencoded"
        headers["accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers["sec-fetch-mode"] = "navigate"
        headers["sec-fetch-user"] = "?1"
        headers["sec-fetch-dest"] = "document"

    if referer:
        headers["referer"] = referer

    # 🔥 USER IP FORWARDING
    if user_ip:
        headers["X-Forwarded-For"] = user_ip
        headers["X-Real-IP"] = user_ip
        headers["X-Originating-IP"] = user_ip
        headers["CF-Connecting-IP"] = user_ip

    return headers


def extract_csrf(html):
    patterns = [
        r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']',
        r'value=["\']([^"\']+)["\']\s+name=["\']_token["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            return m.group(1)
    return None


# ============================================================
# MAIN FLOW
# ============================================================
def process_account(ref_code, user_ip):
    """Register + Login + Task Bypass for 1 account"""
    email = random_email()
    device = random_device()

    result = {
        "email": email,
        "device": f"{device['brand']} {device['model']}",
        "ref_code": ref_code,
        "user_ip": user_ip,
        "steps": [],
        "success": False,
        "status": "FAILED",
        "adjust_url": None,
    }

    try:
        # ============================================
        # STEP 1: REGISTER
        # ============================================
        session = requests.Session()
        signup_url = f"{SIGNUP_URL}?ref={ref_code}"

        r1 = session.get(signup_url, headers=get_headers(device=device, user_ip=user_ip), timeout=TIMEOUT)

        if r1.status_code != 200:
            result["steps"].append(f"Register page HTTP {r1.status_code}")
            return result

        token = extract_csrf(r1.text)
        if not token:
            result["steps"].append("No CSRF token")
            return result

        time.sleep(1)

        data = {
            "_token": token,
            "ref": ref_code,
            "email": email,
            "password": PASSWORD,
            "password_confirmation": PASSWORD,
            "accept_tos": "1"
        }

        r2 = session.post(
            SIGNUP_URL,
            headers=get_headers(referer=signup_url, device=device, user_ip=user_ip),
            data=data,
            cookies=session.cookies.get_dict(),
            timeout=TIMEOUT,
            allow_redirects=False
        )

        if r2.status_code not in [301, 302, 303, 307, 308]:
            result["steps"].append(f"Register failed HTTP {r2.status_code}")
            return result

        result["steps"].append("✅ Registered")

        time.sleep(1.5)

        # ============================================
        # STEP 2: LOGIN
        # ============================================
        r3 = session.get(LOGIN_URL, headers=get_headers(device=device, user_ip=user_ip), timeout=TIMEOUT)
        token = extract_csrf(r3.text)

        if not token:
            result["steps"].append("No login CSRF")
            return result

        time.sleep(1)

        login_data = {"_token": token, "email": email, "password": PASSWORD}
        r4 = session.post(
            LOGIN_URL,
            headers=get_headers(referer=LOGIN_URL, device=device, user_ip=user_ip),
            data=login_data,
            cookies=session.cookies.get_dict(),
            timeout=TIMEOUT,
            allow_redirects=False
        )

        if r4.status_code not in [301, 302, 303, 307, 308]:
            result["steps"].append(f"Login failed HTTP {r4.status_code}")
            return result

        result["steps"].append("✅ Logged in")
        time.sleep(1.5)

        # ============================================
        # STEP 3: CLICK OFFER
        # ============================================
        click_url = f"{BASE_URL}/user/offers/{TARGET_OFFER_ID}/click"
        r5 = session.get(
            click_url,
            headers=get_headers(referer=OFFERS_URL, device=device, user_ip=user_ip),
            timeout=TIMEOUT,
            allow_redirects=False
        )

        if r5.status_code not in [301, 302, 303, 307, 308]:
            result["steps"].append(f"Click failed HTTP {r5.status_code}")
            return result

        current_url = r5.headers.get("Location", "")
        result["steps"].append(f"✅ Redirect 1")

        # Follow chain
        final_url = current_url
        for hop in range(6):
            try:
                r6 = requests.get(
                    current_url,
                    headers={
                        "user-agent": random_ua(device),
                        "x-requested-with": random_xrw(),
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "referer": "https://rewardra.xyz/",
                        "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
                        "X-Forwarded-For": user_ip,
                    },
                    timeout=TIMEOUT,
                    allow_redirects=False
                )

                if r6.status_code in [301, 302, 303, 307, 308]:
                    current_url = r6.headers.get("Location", "")
                    result["steps"].append(f"✅ Redirect {hop+2}")
                    final_url = current_url

                    if "adjust.com" in current_url:
                        result["steps"].append("🎯 Adjust link found")
                        break
                else:
                    break
            except:
                break

        result["adjust_url"] = final_url

        # ============================================
        # STEP 4: TASK BYPASS
        # ============================================
        if "adjust.com" in final_url:
            encoded = quote(final_url, safe="")
            bypass_url = TASK_BYPASS_URL.format(encoded)

            r7 = requests.get(
                bypass_url,
                headers={
                    "user-agent": random_ua(device),
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
                    "X-Forwarded-For": user_ip,
                },
                timeout=TIMEOUT,
                allow_redirects=True
            )

            if r7.status_code == 200:
                result["success"] = True
                result["status"] = "SENT ✓"
                result["steps"].append("✅ Task bypass SENT")
            else:
                result["steps"].append(f"Task bypass HTTP {r7.status_code}")
                result["status"] = f"HTTP {r7.status_code}"
        else:
            result["status"] = "NO_ADJUST"

    except Exception as e:
        result["steps"].append(f"Error: {str(e)[:80]}")

    return result


# ============================================================
# VERCEL HANDLER
# ============================================================
class handler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            ref_code = data.get("ref_code", "").strip()

            if not ref_code:
                self.send_response(400)
                self._set_cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "ref_code required"}).encode())
                return

            # 🔥 USER IP FROM VERCEL
            xff = self.headers.get("x-forwarded-for", "")
            user_ip = xff.split(",")[0].strip() if xff else "unknown"

            # Process 1 account
            result = process_account(ref_code, user_ip)

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.send_response(500)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)[:100]}).encode())
