# Chapter Tracker (Flask & Turso SQLite)

This is a complete rewrite of the Chapter Tracker using Python Flask and SQLite, with the same beautiful UI and features. 
It supports deployment to Vercel as Serverless Functions.

---

## 🚀 The Vercel "Vanishing Data" Fix!

To solve the issue of data vanishing when Vercel goes to sleep, this Flask app is now fully integrated with **Turso (External SQLite)**! This is the exact same database service the original project used.

Because it connects to a database in the cloud, **your data will NEVER vanish**, even on Vercel.

---

## Deployment to Vercel (Simple Steps)

### Step 1 — Create your free database (if you haven't already)
1. Go to https://turso.tech and sign in.
2. Click **New Database** and create one.
3. Copy your **Database URL** (looks like `libsql://your-db.turso.io`).
4. Click **Generate Token** and copy the token.

### Step 2 — Deploy
1. Push this `chapter-tracker-flask` folder to a new GitHub repo.
2. Go to https://vercel.com → **New Project** → import your repo.
3. Before deploying, add these **Environment Variables** in Vercel:
   - `TURSO_DATABASE_URL` = `your-db-url`
   - `TURSO_AUTH_TOKEN` = `your-token`
4. Click **Deploy**.

> That's it! Your app will deploy successfully, and your data is safe forever!

---

## Users & Passwords

| Email | Password |
|-------|----------|
| aibin@gmail.com | aibin123 |
| milan@gmail.com | milan123 |
| edwin@gmail.com | edwin123 |
| seba@gmail.com | seba123 |
| lakshmi@gmail.com | lakshmi123 |
