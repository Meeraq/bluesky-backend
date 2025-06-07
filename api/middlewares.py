import logging
from .models import APILog
logger = logging.getLogger(__name__)


class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            user = request.user if request.user.is_authenticated else None
            log_entry = APILog(path=request.path, method=request.method, user=user)
            log_entry.save()
            logger.info(
                f"API Request: {request.path} | Type: {request.method} | User: {user.username}"
            )
        except:
            pass
        return response

class OriginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            origin =  request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_REFERER')
        except:
            pass
        return response


class TeamsFrameMiddleware:
    """
    Middleware to properly set headers for Microsoft Teams iframes.
    
    This middleware ensures your Django app can be properly embedded
    within Microsoft Teams by setting appropriate headers.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process the request first
        response = self.get_response(request)
        
        # Check if request is from Teams
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_teams = 'teams' in user_agent
        
        # Set headers for all responses to allow embedding in Teams
        # NOTE: For production, you should make this more specific to just Teams domains
        if 'X-Frame-Options' in response:
            del response['X-Frame-Options']
            
        # Allow Teams to frame your app
        response['Content-Security-Policy'] = "frame-ancestors 'self' https://*.teams.microsoft.com https://teams.microsoft.com *.office.com *.office365.com *.sharepoint.com *.microsoft.com;"
        
        return response