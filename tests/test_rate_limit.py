"""Tests for sliding-window rate limiter."""

from __future__ import annotations

from converge_ui.rate_limit import SlidingWindowCounter


class TestSlidingWindowCounter:
    def test_allows_under_limit(self) -> None:
        counter = SlidingWindowCounter(max_requests=5, window_seconds=60.0)
        for _ in range(5):
            assert counter.allow("client-1") is True

    def test_blocks_over_limit(self) -> None:
        counter = SlidingWindowCounter(max_requests=3, window_seconds=60.0)
        for _ in range(3):
            assert counter.allow("client-1") is True
        assert counter.allow("client-1") is False

    def test_separate_keys_independent(self) -> None:
        counter = SlidingWindowCounter(max_requests=2, window_seconds=60.0)
        assert counter.allow("a") is True
        assert counter.allow("a") is True
        assert counter.allow("a") is False
        assert counter.allow("b") is True

    def test_remaining_decreases(self) -> None:
        counter = SlidingWindowCounter(max_requests=5, window_seconds=60.0)
        assert counter.remaining("x") == 5
        counter.allow("x")
        assert counter.remaining("x") == 4
        counter.allow("x")
        assert counter.remaining("x") == 3

    def test_remaining_never_negative(self) -> None:
        counter = SlidingWindowCounter(max_requests=1, window_seconds=60.0)
        counter.allow("x")
        counter.allow("x")
        assert counter.remaining("x") == 0
