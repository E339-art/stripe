"""Tests for auto-pagination helpers."""

from __future__ import annotations

import pytest

from stripewrap.models import Customer, ListResponse
from stripewrap.pagination import async_auto_paging_iter, auto_paging_iter


def _make_customer(i: int) -> dict:
    return {
        "id": f"cus_{i:04d}",
        "object": "customer",
        "created": 1700000000 + i,
        "livemode": False,
    }


def _make_list(customers: list[dict], has_more: bool) -> ListResponse[Customer]:
    return ListResponse[Customer].model_validate(
        {
            "object": "list",
            "data": customers,
            "has_more": has_more,
            "url": "/v1/customers",
        }
    )


class TestAutoPagingIter:
    def test_single_page(self):
        """When has_more is False, only one page is fetched."""
        calls = []

        def list_func(**kwargs):
            calls.append(kwargs)
            return _make_list([_make_customer(1), _make_customer(2)], has_more=False)

        items = list(auto_paging_iter(list_func))

        assert len(items) == 2
        assert len(calls) == 1

    def test_multiple_pages(self):
        """Should automatically follow starting_after across pages."""
        pages = [
            [_make_customer(i) for i in range(3)],
            [_make_customer(i) for i in range(3, 5)],
        ]
        call_count = 0

        def list_func(**kwargs):
            nonlocal call_count
            result = pages[call_count]
            has_more = call_count < len(pages) - 1
            call_count += 1
            return _make_list(result, has_more=has_more)

        items = list(auto_paging_iter(list_func))

        assert len(items) == 5
        assert call_count == 2

    def test_starting_after_is_passed(self):
        """The starting_after cursor should equal the last item's ID."""
        seen_params: list[dict] = []

        page1_customers = [_make_customer(1)]
        page2_customers = [_make_customer(2)]

        def list_func(**kwargs):
            seen_params.append(dict(kwargs))
            if len(seen_params) == 1:
                return _make_list(page1_customers, has_more=True)
            return _make_list(page2_customers, has_more=False)

        list(auto_paging_iter(list_func))

        # Second call should have starting_after set to the first page's last item ID
        assert seen_params[1]["starting_after"] == "cus_0001"

    def test_empty_page(self):
        """Empty data with has_more=True should stop iteration safely."""

        def list_func(**kwargs):
            return _make_list([], has_more=True)

        items = list(auto_paging_iter(list_func))
        assert items == []


class TestAsyncAutoPagingIter:
    async def test_single_page_async(self):
        async def list_func(**kwargs):
            return _make_list([_make_customer(1)], has_more=False)

        items = [item async for item in async_auto_paging_iter(list_func)]
        assert len(items) == 1

    async def test_multiple_pages_async(self):
        call_count = 0
        pages = [
            [_make_customer(i) for i in range(2)],
            [_make_customer(i) for i in range(2, 4)],
        ]

        async def list_func(**kwargs):
            nonlocal call_count
            result = pages[call_count]
            has_more = call_count < len(pages) - 1
            call_count += 1
            return _make_list(result, has_more=has_more)

        items = [item async for item in async_auto_paging_iter(list_func)]
        assert len(items) == 4
        assert call_count == 2
