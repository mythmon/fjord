from fjord.base.tests import TestCase, LocalizingClient, reverse
from nose.tools import eq_

from fjord.feedback import models


class TestFeedback(TestCase):
    client_class = LocalizingClient

    def test_valid_happy(self):
        """Submitting a valid happy form creates an item in the DB.

        Additionally, it should redirect to the Thanks page.
        """
        amount = models.Simple.objects.count()

        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'happy': 1,
            'description': u'Firefox rocks!',
            'url': u'http://mozilla.org/'
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(amount + 1, models.Simple.objects.count())

        feedback = models.Simple.objects.latest(field_name='id')
        eq_(u'Firefox rocks!', feedback.description)
        eq_(u'http://mozilla.org/', feedback.url)
        eq_(True, feedback.happy)

    def test_valid_sad(self):
        """Submitting a valid sad form creates an item in the DB.

        Additionally, it should redirect to the Thanks page.
        """
        amount = models.Simple.objects.count()

        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'happy': 0,
            'description': u"Firefox doesn't make me sandwiches. :("
        })

        self.assertRedirects(r, reverse('thanks'))
        eq_(amount + 1, models.Simple.objects.count())

        feedback = models.Simple.objects.latest(field_name='id')
        eq_(u"Firefox doesn't make me sandwiches. :(", feedback.description)
        eq_(u'', feedback.url)
        eq_(False, feedback.happy)

    def test_invalid_form(self):
        """Submitting a bad form should return an error and not change pages."""
        url = reverse('feedback', args=('firefox.desktop.stable',))
        r = self.client.post(url, {
            'url': 'http://mozilla.org/'
            # No happy/sad
            # No description
        })

        self.assertContains(r, 'This field is required')
        self.assertTemplateUsed(r, 'feedback/feedback.html')

    def test_feedback_router(self):
        """Requesting a generic template should give a feedback form."""
        # TODO: This test might need to change when the router starts routing.
        url = reverse('feedback')
        r = self.client.get(url, HTTP_USER_AGENT='Firefox')
        eq_(200, r.status_code)
        self.assertTemplateUsed(r, 'feedback/feedback.html')

    def test_email_collection(self):
        """If the user enters an email and checks the box, collect the email."""
        email_count = models.SimpleEmail.objects.count()
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email': 'bob@example.com',
            'email_ok': 1,
        })
        eq_(email_count + 1, models.SimpleEmail.objects.count())
        eq_(r.status_code, 302)

    def test_email_privacy(self):
        """If an email is entered, but the box is not checked, don't collect."""
        email_count = models.SimpleEmail.objects.count()
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email': 'bob@example.com',
            'email_ok': 0,
        })
        eq_(email_count, models.SimpleEmail.objects.count())
        eq_(r.status_code, 302)

    def test_email_no_fail(self):
        """If an email is not entered and the box is checked, don't error out."""
        email_count = models.SimpleEmail.objects.count()
        url = reverse('feedback', args=('firefox.desktop.stable',))

        r = self.client.post(url, {
            'happy': 0,
            'description': u"I like the colors.",
            'email_ok': 1,
        })
        eq_(email_count, models.SimpleEmail.objects.count())
        eq_(r.status_code, 302)
