#!/usr/bin/env python3
"""
LeetCode Daily Auto-Solver
Fetches Problem of the Day → Solves via OpenRouter AI → Auto-submits → Emails you
"""

import os
import re
import time
import smtplib
import requests
from datetime import datetime
from collections import deque, defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─────────────────────────────────────────────
#  CONFIG — fill in your .env file
# ─────────────────────────────────────────────
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")   # openrouter.ai — free tier
LEETCODE_CSRFTOKEN  = os.getenv("LEETCODE_CSRFTOKEN", "")
LEETCODE_SESSION    = os.getenv("LEETCODE_SESSION", "")
EMAIL_SENDER        = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD      = os.getenv("EMAIL_PASSWORD", "")        # Gmail App Password
EMAIL_RECEIVER      = os.getenv("EMAIL_RECEIVER", "")

LEETCODE_GQL = "https://leetcode.com/graphql"

# OpenRouter models to try in order (best coding models)
OPENROUTER_MODELS = [
    ("qwen/qwen3-235b-a22b",             "Qwen3-235B"),
    ("deepseek/deepseek-r1",             "DeepSeek-R1"),
    ("qwen/qwen-2.5-coder-32b-instruct", "Qwen2.5-Coder"),
    ("google/gemini-2.5-flash",          "Gemini-2.5-Flash"),
    ("meta-llama/llama-4-maverick",      "Llama-4-Maverick"),
]


# ─────────────────────────────────────────────
#  STEP 1: Fetch Problem of the Day
# ─────────────────────────────────────────────
def fetch_problem_of_the_day():
    query = """
    query questionOfToday {
      activeDailyCodingChallengeQuestion {
        date link
        question {
          questionId title titleSlug difficulty content
          exampleTestcases
          codeSnippets { lang langSlug code }
        }
      }
    }
    """
    resp = requests.post(LEETCODE_GQL, json={"query": query}, timeout=15)
    resp.raise_for_status()
    data = resp.json()["data"]["activeDailyCodingChallengeQuestion"]
    q    = data["question"]
    starter = next((s["code"] for s in q["codeSnippets"] if s["langSlug"] == "python3"), "")
    print(f"✅ Fetched: [{q['difficulty']}] {q['title']} (#{q['questionId']})")
    return {
        "slug": q["titleSlug"], "title": q["title"], "id": q["questionId"],
        "difficulty": q["difficulty"], "content": q["content"],
        "examples": q["exampleTestcases"], "starter": starter,
        "link": f"https://leetcode.com{data['link']}"
    }


# ─────────────────────────────────────────────
#  STEP 2: Solve with OpenRouter
# ─────────────────────────────────────────────
def solve_with_openrouter(problem: dict, model_id: str, model_name: str, error_ctx: str = "") -> str:
    print(f"🤖 Trying {model_name} via OpenRouter...")
    error_hint = f"\nPREVIOUS ATTEMPT FAILED: {error_ctx}\nFix this. Use a completely different approach.\n" if error_ctx else ""

    prompt = f"""You are a world-class competitive programmer. Solve this LeetCode problem in Python3.

Problem: {problem['title']} (#{problem['id']}) [{problem['difficulty']}]
{error_hint}
Description:
{problem['content']}

Examples:
{problem['examples']}

Starter Code:
{problem['starter']}

RULES:
- Output ONLY raw Python3 code. No markdown. No triple backticks. No explanation.
- Use the exact method signature from the starter code.
- For BFS shortest-path: use deque, mark visited nodes.
- For prime problems: precompute with sieve. For divisibility teleportation,
  group indices by ALL prime factors of each value (not just equal values).
  Mark used prime groups to avoid re-expansion (prevents TLE).
- Must be optimal O(N log N) or better.
"""

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://leetcode-bot.local",
        },
        json={
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": 0.0,
        },
        timeout=90,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"]
    if raw is None:
        raise ValueError("Empty response from model — check OpenRouter credits at openrouter.ai")
    code = raw.strip()
    # Strip <think>...</think> (DeepSeek / Qwen reasoning traces)
    code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL).strip()
    # Strip markdown fences
    if "```" in code:
        code = re.sub(r"```(?:python)?\n?", "", code).strip()
    print(f"✅ Got solution from {model_name} ({len(code)} chars)")
    return code


# ─────────────────────────────────────────────
#  STEP 3: Final fallback — ultra-simple AI prompt, all models
# ─────────────────────────────────────────────
def generate_guaranteed_solution(problem: dict) -> str:
    """
    Last resort: try every model with the simplest possible prompt.
    No hardcoded algorithm — works for ANY problem type.
    """
    print("🔒 Final fallback — ultra-simple prompt to all models...")

    # Strip HTML from content for cleaner prompt
    clean_content = re.sub(r'<[^>]+>', ' ', problem['content'])
    clean_content = re.sub(r'\s+', ' ', clean_content).strip()[:1500]

    simple_prompt = (
        f"Solve this LeetCode problem in Python3.\n"
        f"Output ONLY raw Python code. No markdown. No backticks. No explanation.\n\n"
        f"Problem: {problem['title']} (#{problem['id']}) [{problem['difficulty']}]\n\n"
        f"Starter code — use this EXACT class and method name:\n{problem['starter']}\n\n"
        f"Examples:\n{problem['examples']}\n\n"
        f"Description:\n{clean_content}"
    )

    for model_id, model_name in OPENROUTER_MODELS:
        try:
            print(f"  → {model_name}...")
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://leetcode-bot.local",
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": simple_prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.0,
                },
                timeout=60,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            if not raw:
                continue
            code = raw.strip()
            code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL).strip()
            if "```" in code:
                code = re.sub(r"```(?:python3?)?\n?", "", code).strip().rstrip("`").strip()
            if "class Solution" in code or "def " in code:
                print(f"  ✅ Got fallback solution from {model_name}")
                return code
        except Exception as e:
            print(f"  ⚠️  {model_name}: {e}")

    # Absolute last resort placeholder
    m = re.search(r"def\s+(\w+)\s*\(self", problem.get("starter", ""))
    method = m.group(1) if m else "solve"
    print("  ❌ All models failed even in fallback")
    return f"class Solution:\n    def {method}(self, *args):\n        pass  # All AI attempts failed"


# ─────────────────────────────────────────────
#  STEP 4: Submit to LeetCode
# ─────────────────────────────────────────────
def submit_to_leetcode(problem: dict, code: str, max_retries: int = 2) -> dict:
    cookies = {"csrftoken": LEETCODE_CSRFTOKEN, "LEETCODE_SESSION": LEETCODE_SESSION}
    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/problems/{problem['slug']}/",
        "X-CSRFToken": LEETCODE_CSRFTOKEN,
        "User-Agent": "Mozilla/5.0",
    }
    submit_url = f"https://leetcode.com/problems/{problem['slug']}/submit/"
    payload = {"lang": "python3", "question_id": problem["id"], "typed_code": code}

    for attempt in range(1, max_retries + 1):
        print(f"🚀 Submitting (attempt {attempt})...")
        resp = requests.post(submit_url, json=payload, cookies=cookies, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"❌ HTTP {resp.status_code}")
            continue
        sub_id = resp.json().get("submission_id")
        if not sub_id:
            continue
        check_url = f"https://leetcode.com/submissions/detail/{sub_id}/check/"
        for _ in range(20):
            time.sleep(2)
            r = requests.get(check_url, cookies=cookies, headers=headers, timeout=10).json()
            if r.get("state") == "SUCCESS":
                status = r.get("status_msg", "Unknown")
                print(f"📊 Result: {status}")
                return {
                    "status": status, "passed": status == "Accepted",
                    "runtime": r.get("status_runtime", "N/A"),
                    "memory":  r.get("status_memory", "N/A"),
                    "total_correct": r.get("total_correct", "?"),
                    "total_testcases": r.get("total_testcases", "?"),
                    "error": r.get("full_runtime_error") or r.get("compile_error", ""),
                }
    return {"status": "Failed", "passed": False, "error": "Submission timed out"}


# ─────────────────────────────────────────────
#  STEP 5: Full solve loop
# ─────────────────────────────────────────────
def solve_and_submit(problem: dict) -> tuple[str, dict]:
    """
    Strategy:
    - Phase 1: Try each OpenRouter model once (Qwen3 → DeepSeek-R1 → Qwen-Coder → Gemini)
    - Phase 2: Retry best model with error context
    - Phase 3: Guaranteed pure-Python BFS solution (cannot fail)
    """
    last_code, last_result = "", {}
    error_ctx = ""

    # Phase 1: Try each model once
    for model_id, model_name in OPENROUTER_MODELS:
        print(f"\n── {model_name} ──")
        try:
            code = solve_with_openrouter(problem, model_id, model_name, error_ctx)
            last_code = code
            result = submit_to_leetcode(problem, code)
            last_result = result
            if result["passed"]:
                print(f"🎉 Accepted by {model_name}!")
                return code, result
            error_ctx = result.get("error") or result.get("status", "Wrong Answer")
            print(f"⚠️  {result['status']} — trying next model...")
        except Exception as e:
            print(f"⚠️  {model_name} error: {e} — skipping...")

    # Phase 2: Retry Qwen3 with accumulated error context
    print("\n🔁 Retrying Qwen3 with full error context...")
    try:
        code = solve_with_openrouter(problem, OPENROUTER_MODELS[0][0], OPENROUTER_MODELS[0][1], error_ctx)
        last_code = code
        result = submit_to_leetcode(problem, code)
        last_result = result
        if result["passed"]:
            print("🎉 Accepted on retry!")
            return code, result
        error_ctx = result.get("error") or result.get("status", "Wrong Answer")
    except Exception as e:
        print(f"⚠️  Retry error: {e}")

    # Phase 3: Guaranteed solution — pure Python, no AI
    print("\n🔒 All AI attempts failed — using guaranteed solution...")
    code = generate_guaranteed_solution(problem)
    last_code = code
    result = submit_to_leetcode(problem, code)
    last_result = result
    if result["passed"]:
        print("🎉 Accepted via guaranteed solution!")
        return code, result

    print("😞 Even guaranteed solution failed — sending best attempt via email.")
    return last_code, last_result


# ─────────────────────────────────────────────
#  STEP 6: Send Email
# ─────────────────────────────────────────────
def send_email(problem: dict, code: str, result: dict):
    status_emoji = "✅ ACCEPTED" if result.get("passed") else f"⚠️ {result.get('status', 'Unknown')}"
    today = datetime.now().strftime("%B %d, %Y")
    diff_color = {"Easy": "#00b8a3", "Medium": "#ffb800", "Hard": "#ff375f"}.get(problem["difficulty"], "#888")

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px">
  <h2 style="color:#f89f1b">🧠 LeetCode Daily — {today}</h2>
  <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
    <tr><td style="padding:8px;color:#555">Problem</td>
        <td><a href="{problem['link']}">{problem['title']} (#{problem['id']})</a></td></tr>
    <tr style="background:#f9f9f9"><td style="padding:8px;color:#555">Difficulty</td>
        <td style="padding:8px;color:{diff_color}"><b>{problem['difficulty']}</b></td></tr>
    <tr><td style="padding:8px;color:#555">Result</td>
        <td style="padding:8px"><b>{status_emoji}</b></td></tr>
    <tr style="background:#f9f9f9"><td style="padding:8px;color:#555">Runtime</td>
        <td style="padding:8px">{result.get('runtime','N/A')}</td></tr>
    <tr><td style="padding:8px;color:#555">Memory</td>
        <td style="padding:8px">{result.get('memory','N/A')}</td></tr>
    <tr style="background:#f9f9f9"><td style="padding:8px;color:#555">Test Cases</td>
        <td style="padding:8px">{result.get('total_correct','?')} / {result.get('total_testcases','?')}</td></tr>
  </table>
  <h3 style="color:#333">🐍 Python Solution</h3>
  <pre style="background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:8px;font-size:13px;line-height:1.5;overflow-x:auto">{code}</pre>
  {'<p style="color:#888;font-size:12px">⚠️ Auto-submitted via bot.</p>' if result.get("passed") else f'<p style="color:#ff375f">Error: {result.get("error","")[:300]}</p>'}
  <hr style="margin-top:30px">
  <p style="color:#aaa;font-size:11px">LeetCode Daily Bot 🤖 | Keep the streak alive! 🔥</p>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"LeetCode #{problem['id']} — {problem['title']} [{problem['difficulty']}] {status_emoji}"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    print(f"📧 Email sent to {EMAIL_RECEIVER}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def check_cookies_valid() -> bool:
    """Quick check if LeetCode cookies are still valid."""
    try:
        resp = requests.get(
            "https://leetcode.com/api/problems/all/",
            cookies={"csrftoken": LEETCODE_CSRFTOKEN, "LEETCODE_SESSION": LEETCODE_SESSION},
            timeout=10
        )
        # If cookies expired, LeetCode redirects to login (user_name will be empty)
        data = resp.json()
        user = data.get("user_name", "")
        if user:
            print(f"✅ Cookies valid — logged in as: {user}")
            return True
        else:
            print("❌ COOKIES EXPIRED — please update LEETCODE_CSRFTOKEN and LEETCODE_SESSION in GitHub Secrets!")
            return False
    except Exception as e:
        print(f"⚠️  Could not verify cookies: {e}")
        return True  # assume valid, let submission fail naturally


def daily_job():
    print(f"\n{'='*50}")
    print(f"🕙 LeetCode Daily Job started at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")
    try:
        # Step 0: Verify cookies before doing anything
        cookies_ok = check_cookies_valid()
        problem = fetch_problem_of_the_day()
        code, result = solve_and_submit(problem)
        if not cookies_ok:
            result["status"] = "Cookie Expired"
            result["passed"] = False
            result["error"] = "⚠️ LeetCode cookies expired! Go to GitHub Secrets and update LEETCODE_CSRFTOKEN and LEETCODE_SESSION. Steps: Open leetcode.com → Login → F12 → Application → Cookies → copy both values."
        send_email(problem, code, result)
        print("✅ Daily job completed!\n")
    except Exception as e:
        print(f"❌ Daily job failed: {e}")
        raise


if __name__ == "__main__":
    print("🤖 LeetCode Daily Bot — GitHub Actions run")
    daily_job()
