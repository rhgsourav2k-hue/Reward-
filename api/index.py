from flask import Flask, render_template, request, jsonify
import requests
import re
import random
import string
from urllib.parse import quote

app = Flask(__name__, template_folder='../templates')

BASE_URL = "https://rewardra.xyz"
SIGNUP_URL = f"{BASE_URL}/signup"
LOGIN_URL = f"{BASE_URL}/login"
OFFERS_URL = f"{BASE_URL}/user/offers"
PASSWORD = "7797212585@"
TARGET_OFFER_ID = 75926  # WhatsApp Task
TASK_BYPASS_URL = "https://narzo.fun/Adjust/?url={}&submit=SUBMIT"

DEVICES = [
    {"model": "CPH2729", "android": "16", "chrome": "153", "build": "BP2A.250605.015", "brand": "OPPO"},
    {"model": "SM-S928B", "android": "14", "chrome": "120", "build": "UP1A.231005.007", "brand": "samsung"},
    {"model": "Pixel 9 Pro", "android": "15", "chrome": "121", "build": "AP3A.241105.008", "brand": "Google"},
    {"model": "RMX3783", "android": "13", "chrome": "119", "build": "TP1A.220905.001", "brand": "realme"},
    {"model": "V2312", "android": "14", "chrome": "122", "build": "UP1A.231005.007", "brand": "vivo"},
]

def random_device():
    return random.choice(DEVICES)

def random_user_agent(device):
    return f"Mozilla/5.0 (Linux; Android {device['android']}; {device['model']} Build/{device['build']}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{device['chrome']}.0.0.0 Mobile Safari/537.36"

def random_email():
    prefixes = ["user", "acc", "mail", "id", "test", "new", "pro", "app", "web"]
    prefix = random.choice(prefixes)
    letters = ''.join(random.choices(string.ascii_lowercase, k=5))
    digits = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{letters}{digits}@gmail.com"

def get_headers(referer=None, device=None):
    if not device:
        device = random_device()
    headers = {
        "Host": "rewardra.xyz",
        "sec-ch-ua": f'"Android WebView";v="{device["chrome"]}", "Not_A Brand";v="8", "Chromium";v="{device["chrome"]}"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "upgrade-insecure-requests": "1",
        "user-agent": random_user_agent(device),
        "origin": BASE_URL,
        "accept-language": "en-IN,en-US;q=0.9,en;q=0.8",
    }
    if referer:
        headers["referer"] = referer
    return headers

def extract_csrf_token(html):
    m = re.search(r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']', html)
    if m: return m.group(1)
    m = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']', html)
    if m: return m.group(1)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def handle_signup():
    data = request.json
    ref_code = data.get('ref', 'DXWOZZLY').strip()
    
    device = random_device()
    email = random_email()
    session = requests.Session()
    
    try:
        # 1. Register
        r1 = session.get(f"{SIGNUP_URL}?ref={ref_code}", headers=get_headers(device=device), timeout=10)
        if r1.status_code != 200:
            return jsonify({"success": False, "log": f"❌ {email}: Page HTTP {r1.status_code}"})
        
        token = extract_csrf_token(r1.text)
        if not token:
            return jsonify({"success": False, "log": f"❌ {email}: No CSRF token"})
            
        payload = {
            "_token": token,
            "ref": ref_code,
            "email": email,
            "password": PASSWORD,
            "password_confirmation": PASSWORD,
            "accept_tos": "1"
        }
        
        r2 = session.post(SIGNUP_URL, headers=get_headers(referer=f"{SIGNUP_URL}?ref={ref_code}", device=device), data=payload, timeout=10, allow_redirects=False)
        if r2.status_code not in [301, 302, 303, 307, 308]:
            return jsonify({"success": False, "log": f"❌ {email}: Register failed (HTTP {r2.status_code})"})
            
        # 2. Login
        r_login = session.get(LOGIN_URL, headers=get_headers(device=device), timeout=10)
        login_token = extract_csrf_token(r_login.text)
        
        r_login_post = session.post(LOGIN_URL, headers=get_headers(referer=LOGIN_URL, device=device), data={"_token": login_token, "email": email, "password": PASSWORD}, timeout=10, allow_redirects=False)
        if r_login_post.status_code not in [301, 302, 303, 307, 308]:
            return jsonify({"success": False, "log": f"❌ {email}: Login failed"})
            
        # 3. Click Offer
        click_url = f"{BASE_URL}/user/offers/{TARGET_OFFER_ID}/click"
        r_click = session.get(click_url, headers=get_headers(referer=OFFERS_URL, device=device), timeout=10, allow_redirects=False)
        
        adjust_url = r_click.headers.get("Location", "")
        if "adjust.com" not in adjust_url:
            return jsonify({"success": False, "log": f"❌ {email}: Adjust link not found"})
            
        # 4. Task Bypass
        encoded = quote(adjust_url, safe="")
        bypass_url = TASK_BYPASS_URL.format(encoded)
        r_bypass = requests.get(bypass_url, headers={"user-agent": random_user_agent(device)}, timeout=10)
        
        return jsonify({
            "success": True,
            "email": email,
            "log": f"✅ {email} | Device: {device['brand']} {device['model']} | Task {TARGET_OFFER_ID} Bypass Successful!"
        })
        
    except Exception as e:
        return jsonify({"success": False, "log": f"❌ {email}: Error - {str(e)[:40]}"})
