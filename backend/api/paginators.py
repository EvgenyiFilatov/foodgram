from rest_framework.pagination import PageNumberPagination


class CustomPageLimitPagination(PageNumberPagination):
    """Пагинатор с возможностью ограничения вывода рецептов на странице."""
    page_size_query_param = 'limit'
