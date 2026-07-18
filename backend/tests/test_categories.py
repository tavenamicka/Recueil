def test_list_categories_counts_liens(admin_client, lien):
    resp = admin_client.get("/categories")
    assert resp.status_code == 200
    data = resp.json()
    cat = next(c for c in data if c["id"] == lien.categorie_id)
    assert cat["nombre_liens"] == 1


def test_list_categories_requires_auth(client):
    resp = client.get("/categories")
    assert resp.status_code == 401
