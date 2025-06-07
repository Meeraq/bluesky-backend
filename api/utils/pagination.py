# pagination.py
from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Query parameter for custom page size
    max_page_size = 1000  # Optional: maximum allowed page size

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.page = None
        self.queryset = queryset
        page_size = self.get_page_size(request)
        page_number = request.query_params.get('page', 1)
        paginator = self.django_paginator_class(queryset, page_size)

        try:
            self.page = paginator.page(page_number)
        except Exception:
            # If page is invalid, return an empty page
            self.page = paginator.page(1)

        return list(self.page.object_list)
