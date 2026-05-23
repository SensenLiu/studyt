from fastapi.testclient import TestClient

from app.api.main import app


def test_home_page_does_not_render_answer_input_or_answer_fill_logic():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    html = response.text
    assert 'id="answer"' not in html
    assert '参考答案' not in html
    assert 'reference_answer' not in html
