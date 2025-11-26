# linkedin_oauth_backend.py
from flask import Flask, jsonify, request, redirect
import os, requests
import uuid

app = Flask(__name__)

CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("LINKEDIN_REDIRECT_URI", "http://localhost:5000/callback")

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
PROFILE_URL = "https://api.linkedin.com/v2/me"
EMAIL_URL = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"

# Simple in-memory store for demo; replace with DB in prod
_store = {}

@app.route("/auth_url")
def auth_url():
    # scope = "r_liteprofile r_emailaddress"
    # # scope = "r_liteprofile"
    # state = str(uuid.uuid4())
    # url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={scope}&state={state}"
    # return jsonify({"auth_url": url, "state": state})
    import urllib.parse, uuid, os

    state = str(uuid.uuid4())
    scope = "r_liteprofile"
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        # Minimal test — empty scope (diagnostic)
        "scope": scope,
        "state": state
    }
    qs = urllib.parse.urlencode(params, safe='')
    auth_url = f"{AUTH_URL}?{qs}"
    return jsonify({"auth_url": auth_url, "state": state})

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Missing code", 400

    # Exchange code for token
    r = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    })
    r.raise_for_status()
    access_token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}

    prof = requests.get(PROFILE_URL, headers=headers, params={
        "projection": "(id,localizedFirstName,localizedLastName,headline,profilePicture(displayImage~:playableStreams))"
    })
    prof.raise_for_status()
    prof_json = prof.json()

    email = requests.get(EMAIL_URL, headers=headers)
    email.raise_for_status()
    email_json = email.json()

    user = {
        "first_name": prof_json.get("localizedFirstName"),
        "last_name": prof_json.get("localizedLastName"),
        "headline": prof_json.get("headline"),
        "profile": prof_json,
        "email": None
    }

    try:
        elements = email_json.get('elements', [])
        if elements:
            user['email'] = elements[0].get('handle~', {}).get('emailAddress')
    except Exception:
        pass

    lid = prof_json.get('id') or str(uuid.uuid4())
    _store[lid] = user

    # For demo: return JSON with LinkedIn ID so frontend can fetch
    return jsonify({"linkedin_id": lid, "user": user})

@app.route("/profile/<lid>")
def get_profile(lid):
    return jsonify(_store.get(lid, {}))

if __name__ == "__main__":
    app.run(port=5000, debug=True)
