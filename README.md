# 🤖 LeetCode Daily Bot

> Automatically solves and submits LeetCode's Problem of the Day — every day. Emails you the solution. Keeps your streak alive on autopilot. 100% free, forever.

![GitHub Actions](https://img.shields.io/badge/Runs%20On-GitHub%20Actions-blue?logo=github)
![Free](https://img.shields.io/badge/Cost-100%25%20Free-green)
![Python](https://img.shields.io/badge/Python-3.11-yellow?logo=python)
![Models](https://img.shields.io/badge/AI%20Models-10%20Free-purple)

---

## ✨ What it does

Every day automatically:

1. 📥 Fetches LeetCode Problem of the Day (free public API)
2. 🧠 Tries **10 different free AI models** with different algorithmic approaches
3. 🚀 Auto-submits to your LeetCode account until Accepted
4. 🔍 If all 10 fail → scrapes LeetCode discussions for a real solution
5. 📧 Emails you the solution + result every day

---

## 🆓 AI Models Used (all 100% free)

| Attempt | Model | Approach |
|---|---|---|
| 1 | Llama-4-Maverick | Brute force → optimize |
| 2 | Llama-4-Scout | Hash map / dictionary |
| 3 | Llama-3.3-70B | Two pointers |
| 4 | Phi-4 | Binary search |
| 5 | Gemma-3-27B | Dynamic programming |
| 6 | Mistral-7B | Stack / queue |
| 7 | Qwen2.5-7B | Sorting + greedy |
| 8 | DeepSeek-R1-Distill | Sliding window |
| 9 | Phi-3-Medium | Divide and conquer |
| 10 | Hermes-3-405B | Math / bit manipulation |
| 11 | Scrape LeetCode discussions | Real community solutions |

---

## 🚀 Setup (5 minutes)

### Step 1 — Fork this repo
Click the **Fork** button at the top right of this page.

### Step 2 — Get your keys

#### OpenRouter API Key (Free)
1. Go to [openrouter.ai](https://openrouter.ai) → Sign up
2. Click **Keys** → **Create Key** → Copy it (`sk-or-v1-...`)
> No credit card needed. All models used are on the free tier.

#### LeetCode Session Cookies
1. Open [leetcode.com](https://leetcode.com) and **log in**
2. Press **F12** → **Application** tab → **Cookies** → `https://leetcode.com`
3. Copy `csrftoken` and `LEETCODE_SESSION`

> ⚠️ Cookies expire every ~2 weeks. You will need to refresh them.

#### Gmail App Password
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Search **"App Passwords"** → Create one → Copy the 16-char password

---

### Step 3 — Add Secrets to your forked repo

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value |
|---|---|
| `OPENROUTER_API_KEY` | From openrouter.ai → Keys |
| `LEETCODE_CSRFTOKEN` | From browser cookies |
| `LEETCODE_SESSION` | From browser cookies |
| `EMAIL_SENDER` | Your Gmail address |
| `EMAIL_PASSWORD` | Gmail App Password (16 chars) |
| `EMAIL_RECEIVER` | Where to send the daily solution (use Gmail, not college email) |

> ⚠️ Use a personal Gmail as EMAIL_RECEIVER — college emails often block automated mail.

---

### Step 4 — Enable GitHub Actions

1. Go to your forked repo → **Actions** tab
2. Click **"I understand my workflows, enable them"**

---

### Step 5 — Test it!

1. **Actions** tab → **"LeetCode Daily Bot"** → **"Run workflow"** → **"Run workflow"**
2. Watch it run live — completes in under 1 minute usually
3. Check your Gmail for the solution!

---

## 🔧 Maintenance

**Every ~2 weeks** when cookies expire and bot fails:
1. Open leetcode.com → login → F12 → Application → Cookies
2. Copy fresh `csrftoken` and `LEETCODE_SESSION`
3. GitHub → your repo → Settings → Secrets → update both

That's the only maintenance needed. Everything else is automatic.

---

## 💰 Cost breakdown

| Service | Cost |
|---|---|
| GitHub Actions | ✅ Free (2000 min/month, bot uses ~30/month) |
| OpenRouter (all models) | ✅ Free tier — no credits needed |
| Gmail SMTP | ✅ Free |
| LeetCode submission | ✅ Free |
| **Total** | **$0/month forever** |

---

## ⚠️ Disclaimer

Auto-submission is against LeetCode's Terms of Service. Use for personal/educational purposes only. This project is for learning automation and AI integration.
