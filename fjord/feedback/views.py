from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from funfactory.urlresolvers import reverse
from session_csrf import anonymous_csrf_exempt
from mobility.decorators import mobile_template

from fjord.base.util import smart_bool
from fjord.feedback.forms import SimpleForm
from fjord.feedback import models


@mobile_template('feedback/{mobile/}thanks.html')
def thanks(request, template):
    return render(request, template)


def _handle_feedback_post(request):
    form = SimpleForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        # Most platforms aren't different enough between versions to care.
        # Windows is.
        platform = request.BROWSER.platform
        if platform == 'Windows':
            platform += ' ' + request.BROWSER.platform_version

        opinion = models.Simple(
            # Data coming from the user
            happy=data['happy'],
            url=data['url'],
            description=data['description'],
            # Inferred data
            prodchan=_get_prodchan(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            browser=request.BROWSER.browser,
            browser_version=request.BROWSER.browser_version,
            platform=platform,
            locale=request.locale,
        )
        opinion.save()

        if data['email_ok'] and data['email']:
            e = models.SimpleEmail(email=data['email'], opinion=opinion)
            e.save()

        return HttpResponseRedirect(reverse('thanks')), form
    else:
        # The user did something wrong.
        return None, form


def _get_prodchan(request):
    meta = request.BROWSER

    product = ''
    platform = ''
    channel = 'stable'

    if meta.browser == 'Firefox':
        product = 'firefox'
    else:
        product = 'unknown'

    if meta.platform == 'Android':
        platform = 'android'
    elif meta.platform == 'FirefoxOS':
        platform = 'firefoxos'
    elif meta.browser == 'Firefox':
        platform = 'desktop'
    else:
        platform = 'unknown'

    return '{0}.{1}.{2}'.format(product, platform, channel)


def desktop_stable_feedback(request):
    # Use two instances of the same form because the template changes the text
    # based on the value of ``happy``.
    forms = {
        'happy': SimpleForm(initial={'happy': 1}),
        'sad': SimpleForm(initial={'happy': 0}),
    }

    if request.method == 'POST':
        response, form = _handle_feedback_post(request)
        if response:
            return response
        else:
            happy = smart_bool(request.POST.get('happy', None))
            if happy:
                forms['happy'] = form
            else:
                forms['sad'] = form

    return render(request, 'feedback/feedback.html', {'forms': forms})


def mobile_stable_feedback(request):
    form = SimpleForm()
    happy = None
    if request.method == 'POST':
        response, form = _handle_feedback_post(request)
        if response:
            return response
        happy = smart_bool(request.POST.get('happy', None), None)
    return render(request, 'feedback/mobile/feedback.html', {
        'form': form,
        'happy': happy,
    })


feedback_routes = {
    'firefox.desktop.stable': desktop_stable_feedback,
    None: desktop_stable_feedback,
}


@anonymous_csrf_exempt
def feedback_router(request, formname=None, *args, **kwargs):
    view = desktop_stable_feedback
    if request.BROWSER.mobile:
        view = mobile_stable_feedback
    return view(request, *args, **kwargs)
