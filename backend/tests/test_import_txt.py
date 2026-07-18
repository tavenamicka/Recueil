def test_import_txt_creates_liens_and_categorizes(admin_client):
    content = (
        "01/03/2026, 09:15 - jean dupont: Regarde ce truc https://www.youtube.com/watch?v=abc123\n"
        "01/03/2026, 09:16 - jean dupont: Un lien vers facebook https://www.facebook.com/share/xyz\n"
    )
    resp = admin_client.post("/import/txt", files={"file": ("export.txt", content.encode("utf-8"), "text/plain")})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    status = admin_client.get(f"/import/txt/{job_id}").json()
    assert status["status"] == "done"
    assert status["nouveaux"] == 2
    assert status["doublons"] == 0

    liens = admin_client.get("/liens").json()
    assert liens["total"] == 2
    categories = {item["categorie"]["nom"] for item in liens["items"]}
    assert categories == {"Vidéos - YouTube", "Réseaux sociaux - Facebook"}


def test_import_txt_wrong_extension_rejected(admin_client):
    resp = admin_client.post("/import/txt", files={"file": ("export.pdf", b"dummy", "application/pdf")})
    assert resp.status_code == 400


def test_import_txt_requires_auth(client):
    content = "01/03/2026, 09:15 - jean dupont: Un lien https://example.com/x\n"
    resp = client.post("/import/txt", files={"file": ("export.txt", content.encode("utf-8"), "text/plain")})
    assert resp.status_code == 401


def test_import_txt_dedup_on_second_import(admin_client):
    content = "01/03/2026, 09:15 - jean dupont: Lien de test https://example.com/dedup-test\n"
    files = {"file": ("export.txt", content.encode("utf-8"), "text/plain")}

    resp1 = admin_client.post("/import/txt", files=files)
    admin_client.get(f"/import/txt/{resp1.json()['job_id']}")

    resp2 = admin_client.post("/import/txt", files=files)
    status2 = admin_client.get(f"/import/txt/{resp2.json()['job_id']}").json()
    assert status2["doublons"] == 1
    assert status2["nouveaux"] == 0


def test_import_txt_status_not_found(admin_client):
    resp = admin_client.get("/import/txt/unknown-job-id")
    assert resp.status_code == 404
