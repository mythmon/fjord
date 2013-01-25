from django.conf import settings

from fjord.base.browsers import parse_ua


MOBILE_COOKIE = getattr(settings, 'MOBILE_COOKIE', 'mobile')


class ParseUseragentMiddleware(object):
    """Add ``request.BROWSER`` which has information from the User-Agent

    ``request.BROWSER`` has the following attributes:

    - browser: The user's browser, eg: "Firefox".
    - browser_version: The browser's version, eg: "14.0.1"
    - platform: The general platform the user is using, eg "Windows".
    - platform_version: The version of the platform, eg. "XP" or "10.6.2".
    - mobile: If the client is using a mobile device. `True` or `False`.

    Any of the above may be `None` if detection fails.
    """

    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '')
        request.BROWSER = parse_ua(ua)


class MobileQueryStringOverrideMiddleware(object):
    """
    Add querystring override for mobile.

    This allows the user to override mobile detection by setting the
    'mobile=1' or 'mobile=true' in the querystring. This will persist
    in a cookie that other the other middlewares in this file will
    respect.
    """
    def process_request(self, request):
        # The 'mobile' querystring overrides any prior MOBILE
        # figuring and we put it in two places.
        mobile_qs = request.GET.get('mobile', None)
        if mobile_qs == '1':
            request.MOBILE = True
        elif mobile_qs == '0':
            request.MOBILE = False


class MobileMiddleware(object):
    """Set request.MOBILE based on cookies and UA detection."""

    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '')
        mc = request.COOKIES.get(MOBILE_COOKIE)

        if hasattr(request, 'MOBILE'):
            # Our work here is done
            return

        if mc:
            request.MOBILE = (mc == 'yes')
            return

        if hasattr(request, 'BROWSER'):
            # UA Detection already figured this out.
            request.MOBILE = request.BROWSER.mobile
            return

        # Make a guess based on UA if nothing else has figured it out.
        if 'mobile' in ua:
            request.MOBILE = True
        else:
            request.MOBILE = False

    def process_response(self, request, response):
        mobile = getattr(request, 'MOBILE', False)
        response.set_cookie(MOBILE_COOKIE, 'yes' if mobile else 'no')
        return response
