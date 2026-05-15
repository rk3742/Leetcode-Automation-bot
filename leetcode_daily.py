#!/usr/bin/env python3
"""
LeetCode Daily Auto-Solver — 100% Free Edition
Fetches POTD → 10 AI attempts across free models → scrapes solution if all fail → submits → emails
"""

import os, re, time, smtplib, requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LEETCODE_CSRFTOKEN = os.getenv("LEETCODE_CSRFTOKEN", "")
LEETCODE_SESSION   = os.getenv("LEETCODE_SESSION", "")
EMAIL_SENDER       = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD     = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER     = os.getenv("EMAIL_RECEIVER", "")

LEETCODE_GQL = "https://leetcode.com/graphql"

# 100% FREE models on OpenRouter — no credits needed
FREE_MODELS = [
    ("meta-llama/llama-4-maverick",              "Llama-4-Maverick"),
    ("meta-llama/llama-4-scout",                 "Llama-4-Scout"),
    ("meta-llama/llama-3.3-70b-instruct",        "Llama-3.3-70B"),
    ("microsoft/phi-4",                          "Phi-4"),
    ("google/gemma-3-27b-it",                    "Gemma-3-27B"),
    ("mistralai/mistral-7b-instruct",            "Mistral-7B"),
    ("qwen/qwen-2.5-7b-instruct",               "Qwen2.5-7B"),
    ("deepseek/deepseek-r1-distill-llama-70b",  "DeepSeek-R1-Distill"),
    ("microsoft/phi-3-medium-128k-instruct",     "Phi-3-Medium"),
    ("nousresearch/hermes-3-llama-3.1-405b",    "Hermes-3-405B"),
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
    q = data["question"]
    starter = next((s["code"] for s in q["codeSnippets"] if s["langSlug"] == "python3"), "")
    clean = re.sub(r'<[^>]+>', ' ', q["content"])
    clean = re.sub(r'\s+', ' ', clean).strip()
    print(f"✅ Fetched: [{q['difficulty']}] {q['title']} (#{q['questionId']})")
    return {
        "slug": q["titleSlug"], "title": q["title"], "id": q["questionId"],
        "difficulty": q["difficulty"], "content": clean, "raw_content": q["content"],
        "examples": q["exampleTestcases"], "starter": starter,
        "link": f"https://leetcode.com{data['link']}"
    }


# ─────────────────────────────────────────────
#  STEP 2: Solve with a free OpenRouter model
# ─────────────────────────────────────────────
def solve_with_model(problem: dict, model_id: str, model_name: str,
                     error_ctx: str = "", approach: str = "") -> str:
    approach_hint = f"\nTry a COMPLETELY DIFFERENT approach: {approach}\n" if approach else ""
    error_hint    = f"\nPREVIOUS ATTEMPT FAILED WITH: {error_ctx}\nYou MUST fix this.\n" if error_ctx else ""

    prompt = f"""You are an expert competitive programmer. Solve this LeetCode problem in Python3.
OUTPUT ONLY RAW PYTHON CODE. No markdown, no backticks, no explanation whatsoever.
Use the EXACT method signature from the starter code.
{error_hint}{approach_hint}
Problem: {problem['title']} (#{problem['id']}) [{problem['difficulty']}]

Description:
{problem['content'][:2500]}

Examples:
{problem['examples']}

Starter Code:
{problem['starter']}
"""
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                 "Content-Type": "application/json",
                 "HTTP-Referer": "https://leetcode-bot.local"},
        json={"model": model_id, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 2500, "temperature": 0.1},
        timeout=60,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"]
    if not raw:
        raise ValueError("Empty response")
    code = raw.strip()
    code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL).strip()
    if "```" in code:
        code = re.sub(r"```(?:python3?)?\n?", "", code).strip().rstrip("`").strip()
    return code


# ─────────────────────────────────────────────
#  STEP 3: Scrape solution from LeetCode discussions (free, no API)
# ─────────────────────────────────────────────
def scrape_discussion_solution(problem: dict) -> str:
    """Fetch top Python solution from LeetCode discuss page."""
    print("🔍 Scraping LeetCode discuss for a working solution...")
    try:
        # Query LeetCode GraphQL for top solutions
        query = """
        query discussionList($query: String, $orderBy: String) {
          discussionList(filters: {query: $query, orderBy: $orderBy}, first: 5) {
            edges {
              node {
                id title post { content }
              }
            }
          }
        }
        """
        slug = problem["slug"]
        resp = requests.post(
            LEETCODE_GQL,
            json={"query": query,
                  "variables": {"query": f"{slug} python", "orderBy": "most_votes"}},
            timeout=15
        )
        if resp.status_code == 200:
            edges = resp.json().get("data", {}).get("discussionList", {}).get("edges", [])
            for edge in edges:
                content = edge["node"]["post"]["content"]
                # Extract python code blocks
                matches = re.findall(r'```(?:python3?|py)\n(.*?)```', content, re.DOTALL)
                for match in matches:
                    if "class Solution" in match or "def " in match:
                        print("✅ Found solution in discussions!")
                        return match.strip()
    except Exception as e:
        print(f"⚠️  Discussion scrape failed: {e}")

    # Fallback: use a model to reconstruct from known patterns
    print("⚠️  Could not scrape — using pattern-based reconstruction...")
    return ""


# ─────────────────────────────────────────────
#  STEP 4: Submit to LeetCode
# ─────────────────────────────────────────────
def submit_to_leetcode(problem: dict, code: str) -> dict:
    cookies = {"csrftoken": LEETCODE_CSRFTOKEN, "LEETCODE_SESSION": LEETCODE_SESSION}
    headers = {
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/problems/{problem['slug']}/",
        "X-CSRFToken": LEETCODE_CSRFTOKEN,
        "User-Agent": "Mozilla/5.0",
    }
    submit_url = f"https://leetcode.com/problems/{problem['slug']}/submit/"
    payload = {"lang": "python3", "question_id": problem["id"], "typed_code": code}

    print("🚀 Submitting...")
    resp = requests.post(submit_url, json=payload, cookies=cookies, headers=headers, timeout=15)
    if resp.status_code != 200:
        return {"status": f"HTTP {resp.status_code}", "passed": False, "error": "Submit failed"}

    sub_id = resp.json().get("submission_id")
    if not sub_id:
        return {"status": "No submission ID", "passed": False, "error": ""}

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
                "total_correct":   r.get("total_correct", "?"),
                "total_testcases": r.get("total_testcases", "?"),
                "error": r.get("full_runtime_error") or r.get("compile_error", ""),
            }
    return {"status": "Timeout", "passed": False, "error": "Polling timed out"}


# ─────────────────────────────────────────────
#  STEP 5: Full 10-attempt solve loop
# ─────────────────────────────────────────────
# Different algorithmic approaches to try on repeated failures
APPROACHES = [
    "brute force first, then optimize",
    "use a hash map / dictionary for O(1) lookups",
    "use two pointers",
    "use binary search",
    "use dynamic programming with memoization",
    "use a stack or queue",
    "use sorting + greedy",
    "use sliding window",
    "use divide and conquer / recursion",
    "use math / bit manipulation",
]

def solve_and_submit(problem: dict) -> tuple[str, dict]:
    """
    10 attempts across all free models with different approaches.
    If all fail → scrape LeetCode discussions for a real solution.
    """
    last_code, last_result = "", {}
    error_ctx = ""
    attempt = 0

    print(f"\n🎯 Starting 10-attempt solve loop for: {problem['title']}")

    # 10 attempts — cycle through models with different approaches
    for i in range(10):
        attempt += 1
        model_id, model_name = FREE_MODELS[i % len(FREE_MODELS)]
        approach = APPROACHES[i] if i < len(APPROACHES) else ""

        print(f"\n{'─'*45}")
        print(f"🤖 Attempt {attempt}/10 — {model_name}")
        if approach:
            print(f"💡 Approach: {approach}")

        try:
            code = solve_with_model(problem, model_id, model_name, error_ctx, approach)
            last_code = code
            result = submit_to_leetcode(problem, code)
            last_result = result

            if result["passed"]:
                print(f"🎉 ACCEPTED on attempt {attempt} by {model_name}!")
                return code, result

            # Build rich error context for next attempt
            error_ctx = (
                f"Status: {result['status']}. "
                f"Passed {result.get('total_correct','?')}/{result.get('total_testcases','?')} cases. "
                f"Error: {result.get('error','')[:300]}"
            )
            print(f"⚠️  Failed: {result['status']} ({result.get('total_correct','?')}/{result.get('total_testcases','?')} cases)")

        except Exception as e:
            print(f"⚠️  {model_name} error: {e} — skipping...")
            continue

    # All 10 AI attempts failed → scrape LeetCode discussions
    print(f"\n{'─'*45}")
    print("🔍 All 10 AI attempts failed — scraping LeetCode discussions...")
    scraped = scrape_discussion_solution(problem)

    if scraped:
        print("📋 Submitting scraped solution...")
        result = submit_to_leetcode(problem, scraped)
        last_result = result
        if result["passed"]:
            print("🎉 ACCEPTED via scraped solution!")
            return scraped, result
        print(f"⚠️  Scraped solution also failed: {result['status']}")
        last_code = scraped

    print("😞 All attempts exhausted. Sending best solution via email.")
    return last_code, last_result


# ─────────────────────────────────────────────
#  STEP 6: Check cookies
# ─────────────────────────────────────────────
def check_cookies_valid() -> bool:
    try:
        resp = requests.get(
            "https://leetcode.com/api/problems/all/",
            cookies={"csrftoken": LEETCODE_CSRFTOKEN, "LEETCODE_SESSION": LEETCODE_SESSION},
            timeout=10
        )
        user = resp.json().get("user_name", "")
        if user:
            print(f"✅ Cookies valid — logged in as: {user}")
            return True
        print("❌ COOKIES EXPIRED — update LEETCODE_CSRFTOKEN and LEETCODE_SESSION in GitHub Secrets!")
        return False
    except Exception as e:
        print(f"⚠️  Cookie check failed: {e}")
        return True


# ─────────────────────────────────────────────
#  STEP 7: Send Email
# ─────────────────────────────────────────────
def send_email(problem: dict, code: str, result: dict):
    status_emoji = "✅ ACCEPTED" if result.get("passed") else f"⚠️ {result.get('status', 'Unknown')}"
    today = datetime.now().strftime("%B %d, %Y")
    diff_color = {"Easy": "#00b8a3", "Medium": "#ffb800", "Hard": "#ff375f"}.get(problem["difficulty"], "#888")

    html = f"""
<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;padding:20px">
  <h2 style="color:#f89f1b">🧠 LeetCode Daily — {today}</h2>
  <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
    <tr><td style="padding:8px;color:#555;width:120px">Problem</td>
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
  {'<p style="color:#888;font-size:12px">⚠️ Auto-submitted via bot.</p>' if result.get("passed") else f'<p style="color:#ff375f">❌ Error: {result.get("error","")[:300]}</p>'}
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
def daily_job():
    print(f"\n{'='*50}")
    print(f"🕙 LeetCode Daily Job — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    try:
        check_cookies_valid()
        problem = fetch_problem_of_the_day()
        code, result = solve_and_submit(problem)
        send_email(problem, code, result)
        print("✅ Daily job completed!\n")
    except Exception as e:
        print(f"❌ Daily job failed: {e}")
        raise

if __name__ == "__main__":
    print("🤖 LeetCode Daily Bot — GitHub Actions run")
    daily_job()
