"""Claimed — ChatGPT Business Profile Manager."""
import hashlib
import os
import re
import sqlite3
import urllib.parse
from functools import wraps
from pathlib import Path

# Load .env — MUST be first with explicit path
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"[dotenv] Loaded {env_path}")
except ImportError:
    print("[dotenv] python-dotenv not installed")
except Exception as e:
    print(f"[dotenv] Error: {e}")

from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-replace-in-production")
app.config["PROPAGATE_EXCEPTIONS"] = True

DB_PATH = Path(__file__).parent / "claimed.db"


def get_db():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    # Ensure tables exist (Render's ephemeral filesystem)
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, plan TEXT DEFAULT 'free', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    db.execute("CREATE TABLE IF NOT EXISTS scans (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, business_url TEXT NOT NULL, domain TEXT, eligibility TEXT, verification_method TEXT, scan_data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id))")
    return db


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            business_url TEXT NOT NULL,
            domain TEXT,
            eligibility TEXT,
            verification_method TEXT,
            scan_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    db.commit()
    db.close()


# Verification wizard steps per path
WIZARD_STEPS = {
    "shopify": [
        {
            "num": 1,
            "title": "Connect your Shopify store",
            "detail": "Open ChatGPT, go to Business Hub in the sidebar, and select 'Connect with Shopify'. Your store will be verified instantly because Shopify and OpenAI share an integration.",
            "tip": "Make sure you're logged into the same Shopify admin account that owns the store.",
            "link": "https://chatgpt.com",
            "link_text": "Open ChatGPT →",
        },
        {
            "num": 2,
            "title": "Complete Persona identity verification",
            "detail": "After Shopify Connect, OpenAI requires identity verification through Persona. You'll need a government ID and a selfie. This takes about 3 minutes.",
            "tip": "Use a well-lit room and hold your ID steady. Blurry photos cause rejections.",
        },
        {
            "num": 3,
            "title": "Update your business profile",
            "detail": "Once verified, fill in your business description, category, logo, cover photo, delivery policy, and return policy. ChatGPT reviews and publishes changes — this can take a few hours.",
            "tip": "Our AI Profile Optimizer (Pro feature) writes the optimal description for ChatGPT's ranking signals.",
        },
        {
            "num": 4,
            "title": "Add your product feed",
            "detail": "Eligible products from Shopify merchants are already integrated through Shopify Catalog. You can also add a self-service product feed with pricing and availability in Business Hub.",
            "tip": "Products with complete information (price, availability, description) appear more often in ChatGPT recommendations.",
        },
        {
            "num": 5,
            "title": "Monitor your visibility",
            "detail": "Return to your Claimed dashboard to track mentions, website clicks, and keyword appearances in ChatGPT. Set up alerts for changes.",
            "tip": "Insights are aggregated over 28-day windows. Check back weekly to spot trends.",
        },
    ],
    "domain": [
        {
            "num": 1,
            "title": "Sign in to ChatGPT Business Hub",
            "detail": "Go to chatgpt.com, open the sidebar, and click Business Hub. Search for your business by name.",
            "tip": "Use a personal ChatGPT account — you don't need ChatGPT Enterprise or an Ads account.",
            "link": "https://chatgpt.com",
            "link_text": "Open ChatGPT →",
        },
        {
            "num": 2,
            "title": "Verify via business email or domain",
            "detail": "Choose 'Website domain' or 'Business email' verification. Domain verification adds a DNS TXT record. Email sends a code to an address at your domain (e.g., admin@yourbusiness.com).",
            "tip": "DNS verification is faster — it usually confirms within minutes. Email codes expire after 1 hour.",
        },
        {
            "num": 3,
            "title": "Complete Persona identity verification",
            "detail": "Before you can publish changes or view insights, OpenAI requires identity verification through Persona. You'll need a government ID and a selfie. About 3 minutes.",
            "tip": "This step is required even after domain verification. Don't skip it.",
        },
        {
            "num": 4,
            "title": "Optimize your profile",
            "detail": "Add your website, business description, product or service category, logo, and cover photo. OpenAI reviews all changes before publishing — this takes hours, not minutes.",
            "tip": "Be specific in your description. 'Family-owned Italian restaurant in Austin since 1987' beats 'Italian restaurant'.",
        },
        {
            "num": 5,
            "title": "Track your ChatGPT presence",
            "detail": "Use your Claimed dashboard to monitor mentions, clicks, and visibility. We track which keywords surface your business and alert you to changes.",
            "tip": "ChatGPT's responses evolve. Re-check your profile quarterly to keep information current.",
        },
    ],
    "phone": [
        {
            "num": 1,
            "title": "Check if your business is listed",
            "detail": "Sign in to ChatGPT, open Business Hub, and search for your business. US local businesses (stores, restaurants, services) may already have a listing from publicly available data.",
            "tip": "If you can't find your business, you may need to wait — OpenAI is expanding eligibility over time.",
            "link": "https://chatgpt.com",
            "link_text": "Open ChatGPT →",
        },
        {
            "num": 2,
            "title": "Verify by phone or business email",
            "detail": "Choose phone verification (you'll receive a code) or business email verification. OpenAI uses this to confirm you're authorized to manage this business.",
            "tip": "Phone verification is faster. Make sure the phone number is publicly associated with your business.",
        },
        {
            "num": 3,
            "title": "Complete Persona identity verification",
            "detail": "OpenAI requires identity verification through Persona. Have your government ID and a selfie ready. About 3 minutes.",
            "tip": "This is required before you can publish any changes or view insights.",
        },
        {
            "num": 4,
            "title": "Fill in your business details",
            "detail": "Add your hours, address, phone, website, category, description, and photos. Everything you add must be accurate — OpenAI reviews and can reject false information.",
            "tip": "Local businesses should ensure their address and hours are exact. Mismatches slow down approval.",
        },
        {
            "num": 5,
            "title": "Stay visible",
            "detail": "Monitor your Claimed dashboard for ChatGPT mentions and website clicks. Update your profile whenever your hours, menu, or services change.",
            "tip": "Businesses with complete, accurate profiles appear more often. Treat this like your Google Business Profile.",
        },
    ],
}


def analyze_business(url: str) -> dict:
    """Analyze a business URL for ChatGPT profile readiness."""
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    domain = parsed.netloc or parsed.path.split("/")[0]

    signals = []

    # Domain-based signals
    has_shopify = "myshopify.com" in domain or "shopify.com" in domain
    has_www = domain.startswith("www.")
    is_https = parsed.scheme == "https" or url.startswith("https://")

    # TLD signals (strongest indicator for online business)
    commercial_tlds = [".com", ".co", ".io", ".ai", ".shop", ".store"]
    has_commercial_tld = any(domain.endswith(tld) for tld in commercial_tlds)

    # Subdomain signals (local business often uses subdomains or non-www)
    subdomain_parts = domain.replace("www.", "").split(".")
    is_local_likely = len(subdomain_parts) > 2

    # Construct signal list
    if has_shopify:
        signals.append(
            {
                "type": "positive",
                "icon": "shopify",
                "text": "Shopify store detected — eligible for instant verification via Shopify Connect.",
            }
        )

    if has_commercial_tld:
        signals.append(
            {
                "type": "positive",
                "icon": "domain",
                "text": f"Commercial domain ({domain}) — eligible for domain verification.",
            }
        )

    if is_https:
        signals.append(
            {
                "type": "positive",
                "icon": "lock",
                "text": "HTTPS enabled — required for Business Hub verification.",
            }
        )

    if has_www:
        signals.append(
            {
                "type": "neutral",
                "icon": "info",
                "text": "Domain uses www prefix. Ensure your Business Hub claim uses the same domain format.",
            }
        )

    if is_local_likely and not has_shopify:
        signals.append(
            {
                "type": "info",
                "icon": "location",
                "text": "This appears to be a local business. ChatGPT currently supports US local business listings. You may need phone or email verification.",
            }
        )

    # Eligibility verdict
    positive_count = sum(1 for s in signals if s["type"] == "positive")
    if positive_count >= 3:
        eligibility = "ready"
        verdict = "Your business is ready to claim"
        verdict_detail = "You have the key signals for a smooth verification. Start the guided wizard below."
    elif positive_count >= 1:
        eligibility = "possible"
        verdict = "Your business can likely be claimed"
        verdict_detail = "You have some eligibility signals. The guided wizard will help you pick the best verification path."
    else:
        eligibility = "check"
        verdict = "We need more information"
        verdict_detail = "Some signals are unclear from the URL alone. The full scan will check your website for additional eligibility markers."

    # Verification method recommendation
    if has_shopify:
        verification_method = "shopify"
        verification_label = "Shopify Connect — fastest, instant verification"
    elif has_commercial_tld:
        verification_method = "domain"
        verification_label = "Domain verification — email or DNS record"
    else:
        verification_method = "phone"
        verification_label = "Phone or business email verification"

    return {
        "domain": domain,
        "eligibility": eligibility,
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "verification_method": verification_method,
        "verification_label": verification_label,
        "signals": signals,
        "score": positive_count,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    """Debug: test DB connectivity."""
    try:
        db = get_db()
        db.execute("SELECT 1 FROM users LIMIT 1")
        db.close()
        return jsonify({"status": "ok", "db": "connected", "python": os.sys.version})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e), "type": type(e).__name__}), 500


@app.route("/wizard")
def wizard():
    method = request.args.get("method", "domain")
    domain = request.args.get("domain", "your business")
    steps = WIZARD_STEPS.get(method, WIZARD_STEPS["domain"])
    return render_template("wizard.html", method=method, domain=domain, steps=steps)


@app.route("/api/scan", methods=["POST"])
def scan():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "Please enter a business URL"}), 400

    result = analyze_business(url)
    return jsonify(result)


# --- Auth helpers ---

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    salt_hex, dk_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return dk.hex() == dk_hex


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# --- Account routes ---

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            return render_template("signup.html", error="Email and password are required.", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))
        if len(password) < 8:
            return render_template("signup.html", error="Password must be at least 8 characters.", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, hash_password(password)),
            )
            db.commit()
            user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            session["user_id"] = user["id"]
            session["email"] = email
            db.close()
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            db.close()
            return render_template("signup.html", error="An account with this email already exists.")

    return render_template("signup.html", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()
        if user and verify_password(password, user["password_hash"]):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid email or password.", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))

    return render_template("login.html", google_enabled=bool(os.environ.get("GOOGLE_CLIENT_ID")))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/upgrade-me")
@login_required
def upgrade_me():
    """One-click Pro upgrade for testing (remove in production)."""
    db = get_db()
    db.execute("UPDATE users SET plan = 'pro_monthly' WHERE id = ?", (session["user_id"],))
    db.commit()
    db.close()
    return redirect(url_for("optimizer"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", email=session.get("email", ""))


# --- Google OAuth ---

@app.route("/auth/google")
def auth_google():
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not client_id:
        return redirect(url_for("login"))
    redirect_uri = url_for("auth_google_callback", _external=True)
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&redirect_uri={redirect_uri}"
    )
    return redirect(auth_url)


@app.route("/auth/google/callback")
def auth_google_callback():
    import urllib.request, json as _json

    code = request.args.get("code")
    if not code:
        return redirect(url_for("login"))

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return redirect(url_for("login"))

    # Exchange code for token
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": url_for("auth_google_callback", _external=True),
        "grant_type": "authorization_code",
    }).encode()
    token_req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(token_req) as resp:
        token = _json.loads(resp.read())

    # Get user info
    user_req = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token['access_token']}"},
    )
    with urllib.request.urlopen(user_req) as resp:
        user_info = _json.loads(resp.read())

    email = user_info.get("email", "").lower()
    if not email:
        return redirect(url_for("login"))

    # Create or login user
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, "google:" + user_info.get("id", "")),
        )
        db.commit()
        user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    db.close()

    session["user_id"] = user["id"]
    session["email"] = email
    return redirect(url_for("dashboard"))


# --- PayPal Payments ---

PAYPAL_SANDBOX = os.environ.get("PAYPAL_SANDBOX", "true") == "true"
PAYPAL_API_BASE = (
    "https://api-m.sandbox.paypal.com"
    if PAYPAL_SANDBOX
    else "https://api-m.paypal.com"
)
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET", "")

PLANS = {
    "pro_monthly": {"name": "Pro Monthly", "price": "29.00", "currency": "USD"},
    "agency_monthly": {"name": "Agency Monthly", "price": "199.00", "currency": "USD"},
}


def _paypal_auth_header():
    import base64
    credentials = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    return {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}


def _paypal_request(method, path, body=None):
    import urllib.request, json as _json
    url = f"{PAYPAL_API_BASE}{path}"
    data = _json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_paypal_auth_header(), method=method)
    with urllib.request.urlopen(req) as resp:
        return _json.loads(resp.read())


@app.route("/api/paypal/config")
def paypal_config():
    return jsonify({
        "client_id": PAYPAL_CLIENT_ID,
        "sandbox": PAYPAL_SANDBOX,
    })


@app.route("/api/paypal/create-subscription", methods=["POST"])
@login_required
def create_subscription():
    """Create a PayPal subscription for the selected plan."""
    import urllib.request, json as _json

    data = request.get_json()
    plan_key = (data or {}).get("plan", "pro_monthly")
    plan = PLANS.get(plan_key)
    if not plan:
        return jsonify({"error": "Invalid plan"}), 400

    # Create product
    product = _paypal_request("POST", "/v1/catalogs/products", {
        "name": f"Claimed {plan['name']}",
        "type": "SERVICE",
        "category": "SOFTWARE",
    })

    # Create plan
    billing_plan = _paypal_request("POST", "/v1/billing/plans", {
        "product_id": product["id"],
        "name": f"Claimed {plan['name']}",
        "status": "ACTIVE",
        "billing_cycles": [{
            "frequency": {"interval_unit": "MONTH", "interval_count": 1},
            "tenure_type": "REGULAR",
            "sequence": 1,
            "total_cycles": 0,
            "pricing_scheme": {
                "fixed_price": {"value": plan["price"], "currency_code": plan["currency"]}
            },
        }],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "payment_failure_threshold": 3,
        },
    })

    # Create subscription
    subscription = _paypal_request("POST", "/v1/billing/subscriptions", {
        "plan_id": billing_plan["id"],
        "subscriber": {
            "email_address": session.get("email", ""),
        },
        "application_context": {
            "brand_name": "Claimed",
            "locale": "en-US",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "SUBSCRIBE_NOW",
            "return_url": url_for("subscription_success", _external=True),
            "cancel_url": url_for("subscription_cancel", _external=True),
        },
    })

    # Find the approval link
    for link in subscription.get("links", []):
        if link["rel"] == "approve":
            return jsonify({
                "subscription_id": subscription["id"],
                "approval_url": link["href"],
            })

    return jsonify({"error": "No approval link found"}), 500


@app.route("/subscription/success")
@login_required
def subscription_success():
    subscription_id = request.args.get("subscription_id", "")
    plan = request.args.get("plan", "pro_monthly")
    plan_name = PLANS.get(plan, PLANS["pro_monthly"])["name"]

    if subscription_id:
        db = get_db()
        db.execute(
            "UPDATE users SET plan = ? WHERE id = ?",
            (plan, session["user_id"]),
        )
        db.commit()
        db.close()

    return render_template(
        "subscription_success.html",
        plan_name=plan_name,
        subscription_id=subscription_id,
    )


@app.route("/subscription/cancel")
def subscription_cancel():
    return render_template("subscription_cancel.html")


# --- AI Profile Optimizer ---

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

OPTIMIZER_PROMPT = """You are a ChatGPT Business Profile optimization expert. Given a business name and description, generate the optimal profile content for ChatGPT Business Hub.

Output a JSON object with these exact keys:

{
  "profile_description": "A 2-3 sentence business description optimized for ChatGPT's ranking signals. Be specific: include location if provided and what makes the business unique. Use ONLY facts the user provided — never invent years in business, awards, or claims not in the input. If a detail is missing, omit it rather than guessing.",
  "category": "The single best-fitting ChatGPT Business Hub category. Available categories: Retail, Restaurant & Food, Professional Services, Health & Medical, Home Services & Contractors, Automotive, Education & Tutoring, Beauty & Wellness, Financial Services, Technology & Software, Real Estate, Legal Services, Entertainment & Events, Travel & Hospitality, Nonprofit & Community, Sports & Fitness, Arts & Creative, Media & Publishing, Agriculture & Farming, Transportation & Logistics, Manufacturing, Energy & Utilities, Other. Pick the MOST specific one that fits. If the business is a digital agency or SaaS, use Technology & Software. If it's an online store, use Retail. Never default to Other unless truly unclassifiable.",
  "services": ["3-5 specific services or products this business offers, as bullet-friendly one-liners based only on what the user described"],
  "keywords": ["5-8 search terms people would use in ChatGPT to find this business. Include: what they do + location if provided"],
  "business_agent_prompt": "A 1-paragraph prompt for the business's ChatGPT Business Agent. This is what the AI agent uses to answer customer questions. Include: what the business does, who it serves, pricing approach if relevant, what NOT to say, and a friendly tone direction.",
  "profile_tips": ["3 specific tips for this business to improve their ChatGPT visibility, based on current best practices for ChatGPT Business Profiles"]
}

Rules:
- Every field must have real, specific content. No placeholders.
- NEVER invent facts. If the user said 'dentist in Austin', do not add 'serving the community for over 20 years'. If the user didn't mention years, awards, or specific credentials, leave them out.
- Descriptions must pass as written by a human — no AI-slop phrases like 'elevate your experience' or 'cutting-edge solutions.'
- The business_agent_prompt should give the agent clear guardrails.
- Categories: pick the MOST specific match. Digital agency → Technology & Software. Online store → Retail. Plumber → Home Services & Contractors.
- Services should be specific enough that someone searching for them would find this business."""


def _call_openai(system_prompt: str, user_prompt: str) -> dict:
    import urllib.request, json as _json
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured"}

    body = _json.dumps({
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        result = _json.loads(resp.read())

    content = result["choices"][0]["message"]["content"]
    return _json.loads(content)


def _pro_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        db = get_db()
        user = db.execute("SELECT plan FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        db.close()
        if not user or user["plan"] not in ("pro_monthly", "agency_monthly"):
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


@app.route("/optimizer")
@login_required
def optimizer():
    db = get_db()
    user = db.execute("SELECT plan FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    db.close()
    is_pro = user and user["plan"] in ("pro_monthly", "agency_monthly")
    return render_template("optimizer.html", is_pro=is_pro, email=session.get("email", ""))


@app.route("/api/optimize-profile", methods=["POST"])
@_pro_required
def optimize_profile():
    data = request.get_json()
    business_name = (data or {}).get("business_name", "").strip()
    business_description = (data or {}).get("business_description", "").strip()

    if not business_name:
        return jsonify({"error": "Business name is required"}), 400

    user_prompt = f"Business: {business_name}"
    if business_description:
        user_prompt += f"\nDescription: {business_description}"

    try:
        result = _call_openai(OPTIMIZER_PROMPT, user_prompt)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)