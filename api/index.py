from flask import Flask, render_template, request, jsonify
import requests
import re
import random
import string

app = Flask(__name__, template_folder='../templates')

BASE_URL = "https://rewardra.xyz"
SIGNUP_URL = f"{BASE_URL}/signup"
PASSWORD = "7797212585@"

def get_random_email():
    chars = string.ascii_lowercase + string.digits
    prefix = ''.join(random.choice(chars) for _ in range(10))
    return f"{prefix}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com']) }"

def extract_csrf_token(html):
    m = re.search(r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']', html)
    if m:
        return m.group(1)
    m = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']_token["\']', html)
    if m:
        return m.group(1)
    m = re.search(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']', html)
    if m:
        return m.group(1)
    return None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def handle_signup():
    data = request.json
    ref_code = data.get('ref', '').strip()
    count = int(data.get('count', 1))
    
    if not ref_code:
        return jsonify({"success": False, "message": "Referral code is required!"})
    
    if count > 3:
        count = 3

    success_count = 0
    failed_count = 0
    logs = []

    headers = {
        "Host": "rewardra.xyz",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": BASE_URL,
        "Referer": f"{SIGNUP_URL}?ref={ref_code}"
    }

    for i in range(count):
        email = get_random_email()
        session = requests.Session()
        
        try:
            r1 = session.get(f"{SIGNUP_URL}?ref={ref_code}", headers=headers, timeout=10)
            if r1.status_code != 200:
                logs.append(f"❌ {email}: Failed to load page (HTTP {r1.status_code})")
                failed_count += 1
                continue
                
            token = extract_csrf_token(r1.text)
            if not token:
                logs.append(f"❌ {email}: CSRF token not found")
                failed_count += 1
                continue
                
            payload = {
                "_token": token,
                "ref": ref_code,
                "email": email,
                "password": PASSWORD,
                "password_confirmation": PASSWORD,
                "accept_tos": "1"
            }
            
            r2 = session.post(SIGNUP_URL, headers=headers, data=payload, timeout=10, allow_redirects=False)
            
            if r2.status_code in [301, 302, 303, 307, 308] or r2.status_code == 200:
                html_lower = r2.text.lower()
                if "already" in html_lower or "taken" in html_lower:
                    logs.append(f"❌ {email}: Email already taken")
                    failed_count += 1
                elif "captcha" in html_lower:
                    logs.append(f"❌ {email}: Captcha triggered")
                    failed_count += 1
                else:
                    logs.append(f"✅ {email}: Signup Successful!")
                    success_count += 1
            else:
                logs.append(f"❌ {email}: Failed with HTTP {r2.status_code}")
                failed_count += 1
                
        except Exception as e:
            logs.append(f"❌ {email}: Error -> {str(e)[:40]}")
            failed_count += 1

    return jsonify({
        "success": True,
        "success_count": success_count,
        "failed_count": failed_count,
        "logs": logs
    })
