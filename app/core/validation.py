from app.core.errors import BusinessError


def parse_pagination_args(page=1, page_size=20):
    """Validate and normalize the established API pagination contract."""

    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        raise BusinessError("page 和 page_size 必须是整数")
    if page < 1:
        raise BusinessError("page 必须大于等于 1")
    if page_size < 1 or page_size > 100:
        raise BusinessError("page_size 必须在 1 到 100 之间")
    return page, page_size
