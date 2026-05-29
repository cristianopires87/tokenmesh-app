from unittest.mock import patch, MagicMock
from tokenmesh.tracker.tracker import TokenTracker


def _make_tracker(url="http://test:8000"):
    return TokenTracker(collector_url=url)


def _track(tracker):
    return tracker.track(
        provider="openai",
        model="gpt-4o",
        tenant_id="test_tenant",
        project_id="test_project",
        agent_id="test_agent",
        input_tokens=100,
        output_tokens=50,
        latency_ms=200,
    )


def test_track_returns_correct_event():
    tracker = _make_tracker()
    with patch("tokenmesh.tracker.tracker.httpx.Client"):
        event = _track(tracker)

    assert event.input_tokens == 100
    assert event.output_tokens == 50
    assert event.total_tokens == 150
    assert event.estimated_cost > 0
    assert event.provider == "openai"
    assert event.model == "gpt-4o"


def test_track_sends_http_post():
    tracker = _make_tracker()
    with patch("tokenmesh.tracker.tracker.httpx.Client") as MockClient:
        mock_http = MockClient.return_value.__enter__.return_value
        _track(tracker)
        mock_http.post.assert_called_once()
        call_url = mock_http.post.call_args[0][0]
        assert call_url == "http://test:8000/track"


def test_fallback_to_print_on_http_error(capsys):
    tracker = _make_tracker()
    with patch("tokenmesh.tracker.tracker.httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.post.side_effect = Exception("connection refused")
        event = _track(tracker)

    captured = capsys.readouterr()
    assert "gpt-4o" in captured.out
    assert event is not None  # event is still returned even on failure


def test_custom_collector_url():
    tracker = TokenTracker(collector_url="http://custom:9000")
    assert tracker.collector_url == "http://custom:9000"


def test_env_var_sets_collector_url(monkeypatch):
    monkeypatch.setenv("TOKENMESH_COLLECTOR_URL", "http://from-env:7777")
    tracker = TokenTracker()
    assert tracker.collector_url == "http://from-env:7777"


def test_default_collector_url():
    tracker = TokenTracker()
    assert "localhost:8000" in tracker.collector_url
