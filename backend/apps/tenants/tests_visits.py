from django.core.cache import cache
from rest_framework.test import APITestCase

from apps.tenants.models import SiteVisitCounter


class SiteVisitCounterTests(APITestCase):
    def setUp(self):
        cache.clear()
        SiteVisitCounter.objects.update_or_create(pk=1, defaults={'total': 0})

    def test_get_reads_without_incrementing_and_post_increments(self):
        first = self.client.get('/api/site/visitas/')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data, {'total': 0})

        counted = self.client.post('/api/site/visitas/', {}, format='json')
        self.assertEqual(counted.status_code, 200)
        self.assertEqual(counted.data, {'total': 1})
        self.assertEqual(self.client.get('/api/site/visitas/').data, {'total': 1})

    def test_counter_does_not_store_visitor_data(self):
        self.client.post('/api/site/visitas/', {}, format='json', REMOTE_ADDR='10.20.30.40')
        counter = SiteVisitCounter.objects.get(pk=1)
        self.assertEqual(counter.total, 1)
        self.assertEqual({field.name for field in counter._meta.fields}, {'id', 'total', 'atualizado_em'})
