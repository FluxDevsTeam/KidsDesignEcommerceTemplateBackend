@action(detail=False, methods=['get'], url_path='search')
    @swagger_helper(tags="Search", model="Product")
    def search(self, request, *args, **kwargs):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({"count": 0, "next": None, "previous": None, "results": []})

    # Cache key: Query-specific with pagination params
    query_params = dict(request.query_params)
    cache_key = f"product_search:{json.dumps(query_params, sort_keys=True)}"
    cache_timeout = 300  # 5 minutes TTL

    # Check cache
    cached_response = cache.get(cache_key)
    if cached_response:
        return Response(cached_response)

    # Fetch from DB
    queryset = self.get_queryset().filter(
        name__icontains=query
    ) | self.get_queryset().filter(
        sub_category__name__icontains=query
    )  # Example: search name or subcategory
    queryset = queryset.distinct()

    # Apply pagination
    page = self.paginate_queryset(queryset)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
    else:
        serializer = self.get_serializer(queryset, many=True)
        response = Response(serializer.data)

    # Cache the response
    cache.set(cache_key, response.data, cache_timeout)
    return response

@action(detail=False, methods=['get'], url_path='autocomplete')
    @swagger_helper(tags="Search", model="Product")
    def autocomplete(self, request, *args, **kwargs):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])

    # Cache key for suggestions
    cache_key = f"search_suggestions:{query}"
    cache_timeout = 3600  # 1 hour TTL

    # Check cache
    cached_suggestions = cache.get(cache_key)
    if cached_suggestions:
        return Response(cached_suggestions)

    # Fetch from DB (simple example)
    suggestions = Product.objects.filter(name__istartswith=query).values_list('name', flat=True)[:10]
    suggestions = list(set(suggestions))  # Unique terms

    # Cache as a simple list (or use sorted set for scores)
    cache.set(cache_key, suggestions, cache_timeout)
    return Response(suggestions)

