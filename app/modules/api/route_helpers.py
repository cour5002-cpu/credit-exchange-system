from flask import request

from app.core.responses import ok
from app.core.validation import parse_pagination_args
from app.utils.pagination import paginate_query


def paged_response(loader, serializer):
    page, page_size = parse_pagination_args(
        request.args.get("page", 1),
        request.args.get("page_size", 20),
    )
    result = loader(page, page_size)
    return ok({
        "items": [serializer(item) for item in result.items],
        "page": result.page,
        "page_size": result.page_size,
        "total": result.total,
        "pages": result.pages,
    })


def paginate_operation_records(query, page, page_size):
    return paginate_query(query, page, page_size)
