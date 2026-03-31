# 🚀 DocuSense AI + StreamPulse — Complete Setup Guide
## Mac + VS Code + Copilot — Zero to Running

---

## PART 1 — ANSWERS TO YOUR QUESTIONS

### What is the database password in Supabase URL?
When you created your Supabase project, it asked you to set a
"Database Password". That is the password that goes in the URL.

If you forgot it:
→ Supabase Dashboard → Settings → Database → scroll down to
  "Reset database password" → reset it → use the new one

The URL looks like this:
```
postgresql://postgres:YOUR_PASSWORD_HERE@db.abcdefgh.supabase.co:5432/postgres
```
Replace YOUR_PASSWORD_HERE with whatever password you set or reset.

### What is SECRET_KEY?
It is just any random string you make up yourself.
It is used to sign internal tokens. Nobody needs to know it.

Examples you can use right now (pick any one):
```
MyDocuSense2026SecretKey!XyZ9
StreamPulse_Secret_Key_2026_YashR
Yash_Vardhan_Secret_Key_32Chars!
```
Or generate one by running this in Terminal:
```bash
python3.11 -c "import secrets; print(secrets.token_hex(16))"
```
Copy whatever it prints. That is your SECRET_KEY.

---

## PART 2 — ACCOUNTS TO CREATE FIRST (15 minutes)

Do these in your browser before touching VS Code.

### Account 1 — Google Gemini (free, no card)
1. Go to → https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API key"
4. Click "Create API key in new project"
5. Copy the key that appears (starts with "AIza...")
6. Save it somewhere — this is your GEMINI_API_KEY

### Account 2 — Supabase Project 1 "docusense" (free, no card)
1. Go to → https://supabase.com
2. Click "Start your project" → Sign up with GitHub or Google
3. Click "New project"
4. Fill in:
   - Organization: your name
   - Project name: docusense
   - Database password: type something you will remember
     Example: DocuSense2026!
     ⚠️ WRITE THIS DOWN — you need it for the URL
   - Region: Southeast Asia (Singapore) — closest to Jaipur
5. Click "Create new project"
6. Wait 2 minutes for it to finish loading
7. Now collect your credentials:

   **DATABASE_URL:**
   → Settings (gear icon) → Database
   → Scroll to "Connection string" section
   → Click "URI" tab
   → Copy the string shown
   → It looks like: postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres
   → Replace [YOUR-PASSWORD] with the password you typed in step 4
   
   **SUPABASE_URL:**
   → Settings → API
   → Copy "Project URL" (looks like https://abcdefgh.supabase.co)
   
   **SUPABASE_SERVICE_KEY:**
   → Settings → API
   → Under "Project API keys" find "service_role"
   → Click "Reveal" → Copy that long key
   → ⚠️ Use service_role NOT anon key

   **Create Storage Bucket:**
   → Left sidebar → Storage
   → Click "New bucket"
   → Name: docusense-files
   → Toggle: Private (OFF = private)
   → Click "Save"

### Account 3 — Supabase Project 2 "streampulse" (same account)
1. Click the project name dropdown at top → "New project"
2. Fill in:
   - Project name: streampulse
   - Database password: StreamPulse2026!
     ⚠️ WRITE THIS DOWN TOO — different from docusense
   - Region: Southeast Asia (Singapore)
3. Wait 2 minutes
4. Collect same credentials as above (different values this time)
5. Create Storage Bucket:
   → Storage → New bucket → name: streampulse-archive → Private → Save

### Account 4 — Upstash Redis (free, no card)
1. Go to → https://upstash.com
2. Click "Start for free" → Sign up with GitHub or Google
3. Click "Create database"
4. Fill in:
   - Name: myredis
   - Type: Regional
   - Region: AP-South-1 (Mumbai) — closest to Jaipur
   - Click "Create"
5. Click on your database → scroll to "REST API" section
6. Copy:
   - UPSTASH_REDIS_REST_URL (looks like https://xxxx.upstash.io)
   - UPSTASH_REDIS_REST_TOKEN (long string)

### Account 5 — Confluent Cloud Kafka (free, no card)
1. Go to → https://confluent.cloud
2. Click "Try free" → Sign up with Google or email
3. Click "Create cluster"
4. Select "Basic" (the free one) → click "Begin configuration"
5. Select provider: Google Cloud, Region: Singapore
6. Cluster name: streampulse → Click "Launch cluster"
7. Wait 2 minutes for cluster to start
8. Create Topics:
   → Left sidebar → Topics → "Create topic"
   → Topic name: ecommerce-events → Create
   → Create topic again
   → Topic name: ecommerce-dlq → Create
9. Create API Keys:
   → Left sidebar → API keys → "Create key"
   → Select "Global access" → Next → Copy and save:
     - Key (this is KAFKA_API_KEY)
     - Secret (this is KAFKA_API_SECRET)
10. Get Bootstrap Server:
    → Left sidebar → Cluster settings → Endpoints
    → Copy "Bootstrap server" (looks like pkc-xxx.asia-southeast1.gcp.confluent.cloud:9092)
    → This is KAFKA_BOOTSTRAP_SERVERS

### Account 6 — GitHub (free)
1. Go to → https://github.com → Sign up
2. Create repo: click "+" → New repository
   - Name: docusense → Public → Create repository (no README)
3. Create repo again:
   - Name: streampulse → Public → Create repository

---

## PART 3 — FILL IN YOUR .ENV FILES

### DocuSense .env
Open VS Code → open docusense folder → open .env file
Replace every placeholder with your real values:

```
GEMINI_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

DATABASE_URL=postgresql://postgres:DocuSense2026!@db.abcdefgh.supabase.co:5432/postgres

SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXXXXXXXXX
SUPABASE_BUCKET=docusense-files

UPSTASH_REDIS_REST_URL=https://xxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXX

SECRET_KEY=MyDocuSense2026SecretKey!XyZ9
ENVIRONMENT=development
```

### StreamPulse .env
Open streampulse folder → open .env file:

```
KAFKA_BOOTSTRAP_SERVERS=pkc-xxx.asia-southeast1.gcp.confluent.cloud:9092
KAFKA_API_KEY=XXXXXXXXXXXXXXXXXX
KAFKA_API_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
KAFKA_TOPIC_EVENTS=ecommerce-events
KAFKA_TOPIC_DLQ=ecommerce-dlq

DATABASE_URL=postgresql://postgres:StreamPulse2026!@db.xxxxxxxx.supabase.co:5432/postgres

SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXXXXXXXXX
SUPABASE_BUCKET=streampulse-archive

UPSTASH_REDIS_REST_URL=https://xxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## PART 4 — RUN SUPABASE SQL

You must run the SQL to create tables. Do this for both projects.

### For DocuSense:
1. Go to supabase.com → open your "docusense" project
2. Left sidebar → SQL Editor
3. Click "New query"
4. Open the file docusense/supabase_setup.sql in VS Code
5. Select all (Cmd+A) → Copy (Cmd+C)
6. Paste into Supabase SQL editor
7. Click "Run" (green button)
8. You should see: "Success. No rows returned"

### For StreamPulse:
1. Go to supabase.com → open your "streampulse" project
2. Left sidebar → SQL Editor → New query
3. Open streampulse/supabase_setup.sql in VS Code → copy all → paste
4. Click Run → Success

---

## PART 5 — INSTALL TOOLS ON YOUR MAC

Open Terminal (Cmd+Space → type Terminal → Enter)
Copy and run each block:

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After Homebrew installs, run:
```bash
brew install python@3.11 node git
brew install --cask docker visual-studio-code
npm install -g wscat
```

Open Docker Desktop from your Applications folder.
Wait until you see a whale icon in the top menu bar.
That means Docker is ready.

---

## PART 6 — RUN DOCUSENSE

Open Terminal and run:

```bash
cd ~/Desktop/docusense
docker compose up --build
```

First time takes 3-5 minutes (downloading Docker images).
Wait until you see this line in the logs:
```
api-1  | INFO:     Application startup complete.
```

Open a NEW Terminal tab (Cmd+T) and test:

```bash
# Should return: {"status":"ok","service":"docusense-api","version":"1.0.0"}
curl http://localhost:8000/api/v1/health
```

Upload a PDF:
```bash
# Replace the path with any PDF on your Mac
# Example: your college notes, a textbook chapter, any PDF
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@/Users/$(whoami)/Downloads/any_file.pdf"
```

You will get back something like:
```json
{"doc_id":"abc123-...","filename":"any_file.pdf","chunks_created":24,"status":"ready"}
```

Copy that doc_id and ask a question:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this document about?","doc_id":"PASTE_DOC_ID_HERE"}'
```

Open API playground in browser:
```bash
open http://localhost:8000/docs
```

---

## PART 7 — RUN STREAMPULSE

Open a NEW Terminal window (Cmd+N) and run:

```bash
cd ~/Desktop/streampulse
docker compose up --build
```

First time takes 4-6 minutes (Kafka image is large).
Wait until you see:
```
consumer-1  | [Consumer] Started — waiting for messages...
consumer-2  | [Consumer] Started — waiting for messages...
```
Two consumer instances = your consumer group is working.

Open a NEW Terminal tab and test:

```bash
# Check both services are healthy
curl http://localhost:8001/health
curl http://localhost:8002/api/v1/health
```

Open Kafka UI in browser (see topics and messages visually):
```bash
open http://localhost:8090
```

Send 100 events at 10 per second:
```bash
curl -X POST http://localhost:8001/simulate \
  -H "Content-Type: application/json" \
  -d '{"count": 100, "events_per_second": 10}'
```

Send 500 events instantly:
```bash
curl -X POST "http://localhost:8001/simulate/burst?count=500"
```

Simulate a flash sale:
```bash
curl -X POST http://localhost:8001/simulate/scenario/flash_sale
```

See aggregated metrics:
```bash
curl http://localhost:8002/api/v1/metrics/aggregates
```

Connect to live dashboard (updates every 1 second):
```bash
wscat -c ws://localhost:8002/ws/dashboard
# Press Ctrl+C to stop
```

---

## PART 8 — PUSH TO GITHUB

### DocuSense:
```bash
cd ~/Desktop/docusense
git init
git add .
git commit -m "feat: DocuSense AI - RAG pipeline with pgvector, Gemini, Redis, Supabase"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/docusense.git
git push -u origin main
```

### StreamPulse:
```bash
cd ~/Desktop/streampulse
git init
git add .
git commit -m "feat: StreamPulse - Kafka event pipeline with consumer groups and WebSocket dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/streampulse.git
git push -u origin main
```

Replace YOUR_GITHUB_USERNAME with your actual GitHub username.

---

## PART 9 — ADD GITHUB SECRETS (for CI/CD)

For DocuSense repo:
1. GitHub → docusense repo → Settings → Secrets and variables → Actions
2. Click "New repository secret" and add these one by one:

| Name | Value |
|------|-------|
| GEMINI_API_KEY | your Gemini key |
| UPSTASH_REDIS_REST_URL | your Upstash URL |
| UPSTASH_REDIS_REST_TOKEN | your Upstash token |

For StreamPulse repo:
1. GitHub → streampulse repo → Settings → Secrets and variables → Actions
2. Add these:

| Name | Value |
|------|-------|
| KAFKA_API_KEY | your Confluent key |
| KAFKA_API_SECRET | your Confluent secret |
| UPSTASH_REDIS_REST_URL | your Upstash URL |
| UPSTASH_REDIS_REST_TOKEN | your Upstash token |

---

## PART 10 — USEFUL COMMANDS

```bash
# Stop services but keep data
docker compose down

# Stop and delete all data (clean slate)
docker compose down -v

# Watch live logs
docker compose logs -f

# Watch logs of one service only
docker compose logs -f api
docker compose logs -f consumer

# Restart one service after code change
docker compose up --build api

# List all running containers
docker ps
```

---

## PART 11 — COPILOT TIPS FOR THESE PROJECTS

Paste these prompts into Copilot Chat in VS Code to get help:

For DocuSense:
```
This is a FastAPI RAG application using LangChain, pgvector, Gemini, and Supabase.
Help me add streaming responses to the /query endpoint using Server-Sent Events.
```

For StreamPulse:
```
This is a Kafka consumer using confluent-kafka and SQLAlchemy async.
Help me add a /metrics/funnel endpoint that shows page_view → add_to_cart → purchase conversion rates.
```

---

## TROUBLESHOOTING

**"Cannot connect to Docker daemon"**
→ Open Docker Desktop app from Applications folder
→ Wait for whale icon in top menu bar
→ Try again

**"Port 8000 already in use"**
```bash
sudo lsof -i :8000
kill -9 <PID shown>
```

**"ModuleNotFoundError"**
```bash
docker compose up --build api
```

**Kafka consumer not getting messages after sending**
```bash
docker compose restart kafka
# wait 30 seconds
docker compose restart consumer
```

**Supabase connection error**
→ Check your DATABASE_URL password matches what you set
→ Make sure you ran the SQL setup in Supabase SQL editor
→ Check the project ref in the URL matches your project

**Gemini "quota exceeded"**
→ You hit 15 requests/minute (free tier limit)
→ Wait 60 seconds and try again
→ The Redis cache means repeated questions never hit Gemini

**"vector extension not found" error**
→ You forgot to run supabase_setup.sql
→ Go to Supabase → SQL Editor → run the setup SQL file again

