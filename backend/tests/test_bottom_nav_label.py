from fastapi.testclient import TestClient

from app.api.main import app


def test_home_page_uses_chuti_label_for_bottom_nav_and_completion_hint():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert "onclick=\"showPage('practice', this)\"" in html
    assert '>出题\n    </button>' in html
    assert '点下方「出题」可换一道题' in html
    assert '>答题\n    </button>' not in html
    assert '点下方「答题」可换一道题' not in html
