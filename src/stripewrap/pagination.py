"""Auto-pagination helpers for Stripe list endpoints.

Instead of manually handling ``has_more`` and ``starting_after``,
use the auto-paging iterators::

    # Sync
    for customer in client.customers.list_auto_paging(limit=100):
        process(customer)

    # Async
    async for customer in async_client.customers.list_auto_paging(limit=100):
        await process(customer)
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any, TypeVar

from pydantic import BaseModel

from stripewrap.models import ListResponse

T = TypeVar("T", bound=BaseModel)


def auto_paging_iter(
    list_func: Callable[..., ListResponse[T]],
    **params: Any,
) -> Iterator[T]:
    """Synchronously iterate over all pages of a list endpoint.

    Args:
        list_func: A callable that accepts keyword arguments and returns a
            :class:`~stripewrap.models.ListResponse`.
        **params: Query parameters to pass to *list_func* (e.g. ``limit=100``).

    Yields:
        Individual resource objects across all pages.
    """
    params.setdefault("limit", 100)

    while True:
        page: ListResponse[T] = list_func(**params)
        yield from page.data

        if not page.has_more or not page.data:
            break

        # Use the last item's ID as the cursor for the next page
        params["starting_after"] = page.data[-1].id  # type: ignore[attr-defined]


async def async_auto_paging_iter(
    list_func: Callable[..., Any],
    **params: Any,
) -> AsyncIterator[T]:
    """Asynchronously iterate over all pages of a list endpoint.

    Args:
        list_func: An async callable returning a
            :class:`~stripewrap.models.ListResponse`.
        **params: Query parameters passed to *list_func*.

    Yields:
        Individual resource objects across all pages.
    """
    params.setdefault("limit", 100)

    while True:
        page: ListResponse[T] = await list_func(**params)
        for item in page.data:
            yield item

        if not page.has_more or not page.data:
            break

        params["starting_after"] = page.data[-1].id  # type: ignore[attr-defined]
