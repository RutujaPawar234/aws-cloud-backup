"""End-to-end API tests against mocked AWS (S3 + DynamoDB via moto)."""


# ---------------------------------------------------------------- health
def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["aws_configured"] is True
    assert "region" in body


# ---------------------------------------------------------------- register
def test_register_success(client):
    resp = client.post("/auth/register", json={
        "full_name": "Alice", "email": "alice@example.com", "password": "pass123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "alice@example.com"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_duplicate(client):
    payload = {"full_name": "Bob", "email": "bob@example.com", "password": "pass123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_register_invalid_email(client):
    resp = client.post("/auth/register", json={
        "full_name": "X", "email": "nope", "password": "pass123"})
    assert resp.status_code == 422


# ---------------------------------------------------------------- login
def test_login_success(client):
    client.post("/auth/register", json={
        "full_name": "Cara", "email": "cara@example.com", "password": "pass123"})
    resp = client.post("/auth/login", json={
        "email": "cara@example.com", "password": "pass123"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "full_name": "Dan", "email": "dan@example.com", "password": "pass123"})
    resp = client.post("/auth/login", json={
        "email": "dan@example.com", "password": "WRONG"})
    assert resp.status_code == 401


# ---------------------------------------------------------------- files
def test_upload_and_list(client, auth_headers):
    up = client.post("/files/upload", headers=auth_headers,
                     files={"file": ("sample.pdf", b"hello world", "application/pdf")})
    assert up.status_code == 201
    meta = up.json()["file"]
    assert meta["file_name"] == "sample.pdf"
    assert meta["file_size"] == 11
    assert meta["file_type"] == "PDF"
    assert meta["status"] == "Backed Up"
    assert meta["s3_key"].startswith("backups/")

    listing = client.get("/files", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_download_roundtrip(client, auth_headers):
    up = client.post("/files/upload", headers=auth_headers,
                     files={"file": ("a.txt", b"roundtrip-bytes", "text/plain")})
    fid = up.json()["file"]["file_id"]
    dl = client.get(f"/files/{fid}/download", headers=auth_headers)
    assert dl.status_code == 200
    assert dl.content == b"roundtrip-bytes"


def test_file_detail(client, auth_headers):
    up = client.post("/files/upload", headers=auth_headers,
                     files={"file": ("x.txt", b"abc", "text/plain")})
    fid = up.json()["file"]["file_id"]
    d = client.get(f"/files/{fid}", headers=auth_headers)
    assert d.status_code == 200
    assert d.json()["file_id"] == fid


def test_delete(client, auth_headers):
    up = client.post("/files/upload", headers=auth_headers,
                     files={"file": ("d.txt", b"bye", "text/plain")})
    fid = up.json()["file"]["file_id"]
    assert client.delete(f"/files/{fid}", headers=auth_headers).status_code == 200
    assert client.get(f"/files/{fid}/download", headers=auth_headers).status_code == 404
    assert client.get("/files", headers=auth_headers).json() == []


def test_empty_file_rejected(client, auth_headers):
    resp = client.post("/files/upload", headers=auth_headers,
                       files={"file": ("empty.txt", b"", "text/plain")})
    assert resp.status_code == 400


# ---------------------------------------------------- authorization checks
def test_files_require_auth(client):
    assert client.get("/files").status_code == 401
    assert client.post("/files/upload",
                       files={"file": ("x.txt", b"x", "text/plain")}).status_code == 401


def test_user_cannot_access_others_files(client):
    t1 = client.post("/auth/register", json={
        "full_name": "One", "email": "one@example.com", "password": "pass123"
    }).json()["access_token"]
    up = client.post("/files/upload", headers={"Authorization": f"Bearer {t1}"},
                     files={"file": ("secret.txt", b"top secret", "text/plain")})
    fid = up.json()["file"]["file_id"]

    t2 = client.post("/auth/register", json={
        "full_name": "Two", "email": "two@example.com", "password": "pass123"
    }).json()["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}

    assert client.get("/files", headers=h2).json() == []
    assert client.get(f"/files/{fid}/download", headers=h2).status_code == 404
    assert client.delete(f"/files/{fid}", headers=h2).status_code == 404


def test_bad_token_rejected(client):
    assert client.get("/files",
                      headers={"Authorization": "Bearer garbage"}).status_code == 401
