from rest_framework.throttling import AnonRateThrottle


class PedidoCreateThrottle(AnonRateThrottle):
    scope = 'pedido_create'

    def get_rate(self):
        return '5/min'

    def parse_rate(self, rate):
        return 5, 600

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return None
        return super().get_cache_key(request, view)
