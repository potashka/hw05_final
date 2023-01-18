from django.core.paginator import Paginator
from django.conf import settings

QUANTITY_OF_POSTS = settings.QUANTITY_OF_POSTS


def get_page_context(request, posts):
    paginator = Paginator(posts, QUANTITY_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
