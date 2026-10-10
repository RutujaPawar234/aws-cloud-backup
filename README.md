# ☁ AWS Cloud-Based File Backup and Restore Application

A desktop application that backs up files from your computer to **Amazon Web
Services (AWS)** and restores them on demand. Built as a **Cloud Computing ISE
project**.

> Register → Login → Select File → Upload to **S3** → Save metadata to
> **DynamoDB** → View → Restore → Delete cloud backup

---

## Project Title

**AWS Cloud-Based File Backup and Restore Application**

## Problem Statement

Files kept only on one computer are fragile. A disk crash, a lost or stolen
laptop, accidental deletion, or malware can destroy important documents
permanently, because there is just **one copy in one place**.

This project keeps a **second copy in the AWS cloud**. Files are uploaded to
**Amazon S3** and their details are recorded in **Amazon DynamoDB**, so a file
can be restored to any folder later — even after the local copy is gone.

## Objectives

- Securely back up any file from a desktop app to AWS.
- Store file **metadata** (name, size, type, date, status, S3 key) in DynamoDB.
- **View**, **restore (download)** and **delete** cloud backups.
- Keep every user's files **private** to that user.
- Demonstrate a real cloud architecture: desktop → REST API → AWS.

## Features

- 🔐 Register + login (bcrypt-hashed passwords, JWT tokens — never plain text)
- ⬆ Back up any file via a native file picker, with confirmation
- 📊 Dashboard: total files, storage used, recent backups
- 🗂 Backup history with **search**, **refresh**, per-file **Restore** / **Delete**
- ⬇ Restore to any folder, with "file already exists → replace?" prompt
- 🗑 Delete a **cloud** backup (never touches your local file)
- 👤 Per-user isolation — you only ever see your own files

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Desktop UI | Python 3.11+, **CustomTkinter** |
| Backend API | **FastAPI**, Uvicorn |
| Auth | JWT (python-jose) + bcrypt |
| AWS SDK | **boto3** |
| Cloud Storage | **Amazon S3** |
| Cloud Database | **Amazon DynamoDB** |
| Cloud Security | **AWS IAM** |
| Hosting | Render (Docker) |
| Testing | pytest + **moto** (mocks AWS) |

## AWS Services Used

### Amazon S3
Object storage that holds the actual backup files, under keys like
`backups/<user_id>/<unique>__<file name>`.

### Amazon DynamoDB (metadata — optional)
A NoSQL database that stores file **metadata** (and user accounts). Files use
`user_id` as the partition key so a user's files are fetched in one fast query.
The DynamoDB implementation ships in `server/services/dynamodb_service.py`.

> **Note:** some managed/lab AWS accounts block DynamoDB via an Organizations
> Service Control Policy. For those accounts this project stores the same
> metadata as JSON objects **inside the S3 bucket** instead
> (`server/services/metadata_service.py`), so everything runs with S3 alone.
> The active backend is selected by a single import in `auth_service.py` and
> `routes/files.py`. Layout when using the S3 backend:
> ```
> users/<email>.json                 -> account record
> metadata/<user_id>/<file_id>.json  -> file metadata
> backups/<user_id>/<uuid>__<name>   -> the file bytes
> ```

### AWS IAM
Controls which AWS resources the backend may touch. The app uses an **IAM user**
(never the root account) limited to just the S3 and DynamoDB actions it needs.

### Render
Hosts the FastAPI backend so the desktop app talks to a cloud URL, not localhost.

## Architecture

```text
            USER
              │
              ▼
   ┌────────────────────────┐
   │ Python Desktop App     │
   │ CustomTkinter          │
   └───────────┬────────────┘
               │ HTTPS REST API (JWT)
               ▼
   ┌────────────────────────┐
   │ FastAPI Backend        │   ← hosted on Render
   │ upload / download /    │
   │ delete / metadata      │
   └───────────┬────────────┘
               │ AWS SDK (boto3)
        ┌──────┴───────┐
        ▼              ▼
  ┌──────────┐   ┌──────────────┐
  │ Amazon S3│   │  DynamoDB    │
  │  files   │   │  metadata    │
  └──────────┘   └──────────────┘
      (IAM controls all access)
```

## Workflow

```text
Select File → Desktop App → FastAPI API → Amazon S3 → DynamoDB Metadata
```

1. Login → backend returns a signed JWT.
2. Pick file → app sends it to `POST /files/upload` with the token.
3. Backend uploads bytes to **S3**, writes a metadata item to **DynamoDB**.
4. Dashboard/History read `GET /files` (only that user's items).
5. Restore → `GET /files/{id}/download` streams the bytes back; app saves them.
6. Delete → `DELETE /files/{id}` removes the S3 object + the DynamoDB item.

## Setup — AWS (step by step, AWS Console)

> You can do this by hand in the Console (below), **or** run the optional helper
> `python -m scripts.setup_aws` after filling `.env` — it creates the same
> resources and never deletes anything.

**A. Create an IAM user (not root):**
1. AWS Console → **IAM** → **Users** → **Create user** (e.g. `backup-app`).
2. Do **not** give console access; you only need programmatic keys.
3. Attach a policy with just the actions below (create a custom policy):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "S3Backup",
         "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
         "Resource": [
           "arn:aws:s3:::YOUR_BUCKET_NAME",
           "arn:aws:s3:::YOUR_BUCKET_NAME/*"
         ]
       },
       {
         "Sid": "DynamoBackup",
         "Effect": "Allow",
         "Action": [
           "dynamodb:PutItem", "dynamodb:GetItem",
           "dynamodb:Query", "dynamodb:DeleteItem"
         ],
         "Resource": [
           "arn:aws:dynamodb:*:*:table/BackupFiles",
           "arn:aws:dynamodb:*:*:table/BackupUsers"
         ]
       }
     ]
   }
   ```
4. After creating the user → **Security credentials** → **Create access key**
   (Application running outside AWS). Copy the **Access key ID** and **Secret**.

**B. Create the S3 bucket:**
- **S3** → **Create bucket** → unique name (e.g. `yourname-cloud-backup`) →
  region `ap-south-1` → keep **Block all public access ON** → Create.

**C. Create the DynamoDB tables:**
- **DynamoDB** → **Create table**
  - Table `BackupUsers`, partition key `email` (String).
  - Table `BackupFiles`, partition key `user_id` (String), sort key `file_id` (String).
  - Capacity: **On-demand**.

## Environment Variables

Copy `.env.example` to `.env` and fill it:

```env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
S3_BUCKET_NAME=yourname-cloud-backup
DYNAMODB_TABLE_NAME=BackupFiles
DYNAMODB_USERS_TABLE=BackupUsers
JWT_SECRET=<python -c "import secrets; print(secrets.token_hex(32))">
ACCESS_TOKEN_EXPIRE_MINUTES=720
```

## Local Run

```bash
cd aws-cloud-backup
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows (PowerShell)
# source .venv/bin/activate         # macOS / Linux
pip install -r requirements.txt

# (optional) create the AWS resources automatically:
python -m scripts.setup_aws

# Terminal 1 — backend
uvicorn server.main:app --reload
#   open http://127.0.0.1:8000/docs  and check GET /health

# Terminal 2 — desktop app
python -m client.main
```

> Point the app at a deployed backend with an env var before launching:
> `set BACKEND_URL=https://your-api.onrender.com` (Windows) /
> `export BACKEND_URL=...` (macOS/Linux).

## AWS Configuration (summary)

IAM user (scoped) → access keys → `.env`. S3 bucket (private) for files.
DynamoDB tables `BackupUsers` + `BackupFiles` for metadata. Region configurable
via `AWS_REGION`. Nothing is hard-coded; the desktop app holds no AWS secret.

## Deployment (Render)

1. Push to GitHub.
2. Render → **New + → Web Service → Dockerfile** (or **Blueprint** via
   `render.yaml`).
3. Set the env vars from above in the Render dashboard (`JWT_SECRET` can be
   auto-generated). Keep AWS keys secret.
4. Deploy → get `https://aws-cloud-backup-api.onrender.com` → check `/health`.
5. Launch the app with `BACKEND_URL` set to that URL.

## Testing

```bash
pytest -v
```
Tests use **moto** to mock S3 + DynamoDB, so they run the real boto3 code paths
**offline** — no AWS account needed. Coverage: health, register, login, upload,
list, detail, download round-trip, delete, empty-file reject, auth required,
cross-user isolation, bad-token reject.

## Future Scope

Scheduled auto-backup · folder backup · client-side encryption · file
versioning · email notifications · multi-device sync · file sharing · retention
policies · storage quotas.

## Conclusion

A complete, working AWS cloud application in a real client–server design: a
CustomTkinter desktop client, a FastAPI REST backend, and AWS (S3 + DynamoDB +
IAM) for cloud storage, database and security. It demonstrates the core value of
cloud computing — durable, remote, on-demand, secure storage — in a form simple
to build, run and demonstrate live.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
