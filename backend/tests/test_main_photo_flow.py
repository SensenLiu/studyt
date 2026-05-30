from fastapi.testclient import TestClient

from app.api.main import app


def test_home_page_uses_unified_photo_entry_and_branch_actions():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert "📷 拍题" in html
    assert "立即做题" in html
    assert "保存到错题集" in html
    assert "拍题加入" not in html
    assert "/api/photo-drafts" in html


def test_home_page_shows_category_and_image_actions_in_mistake_cards():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert "系统分类" in html
    assert "查看原图" in html
