from dataclasses import dataclass


@dataclass
class PageResult:
    items: list
    page: int
    page_size: int
    total: int
    pages: int


def paginate_query(query, page, page_size):
    total = query.order_by(None).count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    pages = (total + page_size - 1) // page_size if total else 0
    return PageResult(items=items, page=page, page_size=page_size, total=total, pages=pages)


def finish_query(query, page=None, page_size=None):
    if page is None or page_size is None:
        return query.all()
    return paginate_query(query, page, page_size)
