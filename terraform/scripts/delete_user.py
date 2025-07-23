import os
import requests

# === Config ===
BASE_URL = "https://csp.infoblox.com"
EMAIL = os.getenv("INFOBLOX_EMAIL")
PASSWORD = os.getenv("INFOBLOX_PASSWORD")
SANDBOX_ID_FILE = "sandbox_id.txt"
USER_ID_FILE = "user_id.txt"

# === Validate Inputs ===
if not all([EMAIL, PASSWORD]):
    raise RuntimeError("❌ Missing INFOBLOX_EMAIL or INFOBLOX_PASSWORD")

# === Step 1: Authenticate ===
auth_url = f"{BASE_URL}/v2/session/users/sign_in"
auth_resp = requests.post(auth_url, json={"email": EMAIL, "password": PASSWORD})
auth_resp.raise_for_status()
jwt = auth_resp.json()["jwt"]
headers = {
    "Authorization": f"Bearer {jwt}",
    "Content-Type": "application/json"
}
print("✅ Logged in.")

# === Step 2: Switch Account ===
with open(SANDBOX_ID_FILE, "r") as f:
    sandbox_id = f.read().strip()
switch_url = f"{BASE_URL}/v2/session/account_switch"
switch_payload = {"id": f"identity/accounts/{sandbox_id}"}
switch_resp = requests.post(switch_url, headers=headers, json=switch_payload)
switch_resp.raise_for_status()
jwt = switch_resp.json()["jwt"]
headers["Authorization"] = f"Bearer {jwt}"
print(f"🔁 Switched to sandbox account {sandbox_id}")

# === Step 3: Read user ID ===
if not os.path.exists(USER_ID_FILE):
    print(f"⚠️ User ID file '{USER_ID_FILE}' not found. Skipping deletion.")
    exit(0)

with open(USER_ID_FILE, "r") as f:
    user_id = f.read().strip()

if not user_id:
    print("⚠️ user_id.txt is empty.")
    exit(0)

user_url = f"{BASE_URL}/v2/users/identity/users/{user_id}"

# === Step 4: Delete user ===
try:
    print(f"🗑️ Deleting user {user_id}...")
    resp = requests.delete(user_url, headers=headers)
    if resp.status_code == 204:
        print("✅ User deleted successfully.")
        os.remove(USER_ID_FILE)
    else:
        print(f"❌ Failed to delete user. Status: {resp.status_code}")
        print(resp.text)
except Exception as e:
    print(f"❌ Error during deletion: {e}")
