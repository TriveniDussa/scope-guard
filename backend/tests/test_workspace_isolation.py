from fastapi import status


def test_strict_workspace_isolation(client):
    # 1. Sign up Agency 1 (Alpha Agency)
    alpha_payload = {
        "agency_name": "Alpha Agency",
        "email": "lead@alpha.com",
        "password": "AlphaPassword123!",
        "full_name": "Alice Lead",
    }
    alpha_resp = client.post("/api/v1/auth/signup", json=alpha_payload)
    assert alpha_resp.status_code == status.HTTP_201_CREATED
    alpha_data = alpha_resp.json()
    alpha_token = alpha_data["access_token"]
    alpha_workspace_id = alpha_data["workspace"]["id"]
    alpha_user_id = alpha_data["user"]["id"]

    # 2. Sign up Agency 2 (Beta Agency)
    beta_payload = {
        "agency_name": "Beta Agency",
        "email": "director@beta.com",
        "password": "BetaPassword123!",
        "full_name": "Bob Director",
    }
    beta_resp = client.post("/api/v1/auth/signup", json=beta_payload)
    assert beta_resp.status_code == status.HTTP_201_CREATED
    beta_data = beta_resp.json()
    beta_token = beta_data["access_token"]
    beta_workspace_id = beta_data["workspace"]["id"]
    beta_user_id = beta_data["user"]["id"]

    # Invariant: Workspaces must have different UUIDs
    assert alpha_workspace_id != beta_workspace_id

    # 3. Query users as Alpha Agency
    alpha_users_resp = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {alpha_token}"},
    )
    assert alpha_users_resp.status_code == status.HTTP_200_OK
    alpha_users = alpha_users_resp.json()
    alpha_user_ids = [u["id"] for u in alpha_users]

    # Verify Alpha only sees its own user
    assert alpha_user_id in alpha_user_ids
    assert beta_user_id not in alpha_user_ids

    # 4. Query users as Beta Agency
    beta_users_resp = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {beta_token}"},
    )
    assert beta_users_resp.status_code == status.HTTP_200_OK
    beta_users = beta_users_resp.json()
    beta_user_ids = [u["id"] for u in beta_users]

    # Verify Beta only sees its own user
    assert beta_user_id in beta_user_ids
    assert alpha_user_id not in beta_user_ids

    # 5. Verify /auth/me returns the exact workspace tied to each token
    alpha_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {alpha_token}"}).json()
    beta_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {beta_token}"}).json()

    assert alpha_me["workspace"]["id"] == alpha_workspace_id
    assert alpha_me["workspace"]["name"] == "Alpha Agency"
    assert beta_me["workspace"]["id"] == beta_workspace_id
    assert beta_me["workspace"]["name"] == "Beta Agency"
