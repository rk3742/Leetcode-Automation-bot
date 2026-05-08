# 🤖 LeetCode Daily Bot

> Automatically solves and submits LeetCode's Problem of the Day — every day at 10:30 AM IST. Emails you the solution. Keeps your streak alive on autopilot.

![GitHub Actions](https://img.shields.io/badge/Runs%20On-GitHub%20Actions-blue?logo=github)
![Free](https://img.shields.io/badge/Cost-100%25%20Free-green)
![Python](https://img.shields.io/badge/Python-3.11-yellow?logo=python)

---

## ✨ What it does

Every day at **10:30 AM IST**, automatically:

1. 📥 Fetches LeetCode Problem of the Day (public API)
2. 🧠 Solves it using **Qwen3-235B** via OpenRouter AI
3. 🚀 Auto-submits to your LeetCode account
4. 📧 Emails you the solution + result
5. 🔁 If one AI fails → tries DeepSeek-R1 → Qwen2.5-Coder → Gemini → guaranteed fallback

---

## 🚀 Setup (5 minutes)

### Step 1 — Fork this repo
Click the **Fork** button at the top right of this page.

### Step 2 — Get your API keys

#### OpenRouter API Key (Free)
1. Go to [openrouter.ai](https://openrouter.ai) → Sign up
2. Click **Keys** → **Create Key** → Copy it (`sk-or-v1-...`)

#### LeetCode Session Cookies
1. Open [leetcode.com](https://leetcode.com) and **log in**
2. Press **F12** → Go to **Application** tab → **Cookies** → `https://leetcode.com`
3. Copy the value of `csrftoken`
4. Copy the value of `LEETCODE_SESSION`

> Cookies expire every ~2 weeks. You will need to refresh them.

#### Gmail App Password
1. Go to myaccount.google.com/security
2. Enable **2-Step Verification**
3. Search "App Passwords" → Create one → Copy the 16-char password

---

### Step 3 — Add Secrets to your forked repo

Go to your forked repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Where to get it |
|---|---|
| `OPENROUTER_API_KEY` | openrouter.ai → Keys |
| `LEETCODE_CSRFTOKEN` | Browser → F12 → Cookies |
| `LEETCODE_SESSION` | Browser → F12 → Cookies |
| `EMAIL_SENDER` | Your Gmail address |
| `EMAIL_PASSWORD` | Gmail App Password (16 chars) |
| `EMAIL_RECEIVER` | Email where you want solutions sent |

---

### Step 4 — Enable GitHub Actions

1. Go to your forked repo → **Actions** tab
2. Click **"I understand my workflows, enable them"**

---

### Step 5 — Test it now!

1. Go to **Actions** tab → **"LeetCode Daily Bot"** on the left
2. Click **"Run workflow"** → **"Run workflow"** (green button)
3. Watch it run — completes in ~3 minutes
4. Check your email for the solution!

---

## Maintenance

**Cookies expire every ~2 weeks.** When the bot fails:
1. Open leetcode.com → log in → F12 → Cookies
2. Copy fresh `csrftoken` and `LEETCODE_SESSION`
3. GitHub → your repo → Settings → Secrets → update both values

---

## AI Fallback Chain

```
1st → Qwen3-235B       (best reasoning, free)
2nd → DeepSeek-R1      (best coding benchmark)
3rd → Qwen2.5-Coder    (specialized for code)
4th → Gemini-2.5-Pro   (Google's best)
5th → Retry with error context
6th → Guaranteed pure-Python solution (cannot fail)
```

---

## Cost: $0/month

GitHub Actions (free) + OpenRouter free tier + Gmail SMTP (free) = totally free.

---

## Disclaimer

Auto-submission is against LeetCode ToS. Use for personal/educational purposes only.
