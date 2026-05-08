# 🤖 LeetCode Daily Bot — Setup Guide

## What it does
Every day at **10:30 AM**:
1. 📥 Fetches LeetCode Problem of the Day (free public API)
2. 🧠 Sends it to Groq AI (llama3-70b) to get an optimal Python solution
3. 🚀 Auto-submits to LeetCode using your session cookies
4. 🔁 If wrong answer → re-prompts AI with error context, retries up to 3x
5. 📧 Emails you the solution + result (Accepted/Failed)

---

## ⚙️ Step-by-Step Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your Groq API Key (FREE)
- Go to [console.groq.com](https://console.groq.com)
- Sign up → Create API Key → Copy it

### 3. Get your LeetCode Session Cookies
> ⚠️ These expire every ~2 weeks. You'll need to refresh them.

1. Open [leetcode.com](https://leetcode.com) and **login**
2. Press **F12** → Go to **Application** tab → **Cookies** → `https://leetcode.com`
3. Find and copy:
   - `csrftoken` → paste as `LEETCODE_CSRFTOKEN`
   - `LEETCODE_SESSION` → paste as `LEETCODE_SESSION`

### 4. Get Gmail App Password
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (required)
3. Search "App Passwords" → Create one for "Mail"
4. Copy the 16-character password

### 5. Set up your .env file
```bash
cp .env.example .env
# Edit .env with your actual values
nano .env
```

### 6. Load .env and run the bot
```bash
# Option A: Using python-dotenv (recommended)
python -c "from dotenv import load_dotenv; load_dotenv()" && python leetcode_daily.py

# Option B: Export manually
export $(cat .env | xargs) && python leetcode_daily.py
```

### 7. Test immediately (optional)
In `leetcode_daily.py`, uncomment line 165:
```python
# daily_job()   ← remove the #
```
Run once to verify everything works, then comment it back.

---

## 🖥️ Run it 24/7 (Keep Streak Alive)

### Option A: Linux/Mac — run in background
```bash
nohup python leetcode_daily.py &> bot.log &
```

### Option B: Free Cloud Hosting
Deploy on [Railway.app](https://railway.app) or [Render.com](https://render.com) for free.
- Upload your files
- Set environment variables in the dashboard
- It runs 24/7 without your laptop being on

### Option C: Windows Task Scheduler
- Create a task that runs `python leetcode_daily.py` at startup

---

## 📧 What the Email Looks Like

You'll get a daily email with:
- ✅ Problem title, difficulty, link
- 📊 Submission result (Accepted / runtime / memory)
- 🐍 Full Python solution code

---

## ⚠️ Important Notes

| Topic | Detail |
|-------|--------|
| LeetCode ToS | Auto-submission is against ToS. Low risk if used personally at low frequency. |
| Cookie expiry | `LEETCODE_SESSION` expires ~every 2 weeks. Update `.env` when it does. |
| Groq rate limits | Free tier: 30 req/min — more than enough for 1 problem/day |
| Streak safety | The bot submits at 10:30 AM IST. LeetCode streak resets at midnight UTC (5:30 AM IST) |

---

## 🔧 Troubleshooting

**"401 Unauthorized" on submit** → Your cookies expired. Re-fetch from browser.

**"Module not found"** → Run `pip install -r requirements.txt`

**Email not sending** → Make sure you're using an App Password, not your Gmail password.

**AI gives wrong answer** → The bot auto-retries up to 3 times with error context. If still failing, the email will contain the best attempt.
# Leetcode-Automation-bot
