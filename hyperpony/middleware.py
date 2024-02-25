from asyncio import iscoroutinefunction

from django.utils.decorators import sync_and_async_middleware

from hyperpony.response_handler import process_response


@sync_and_async_middleware
def HyperponyMiddleware(get_response):  # noqa: N802
    if iscoroutinefunction(get_response):

        async def middleware(request):
            response = await get_response(request)
            response = process_response(request, response)
            return response

    else:

        def middleware(request):
            response = get_response(request)
            response = process_response(request, response)
            return response

    return middleware
