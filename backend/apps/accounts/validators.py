import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    def validate(self, password, user=None):
        requirements = (
            (r'[A-Z]', _('A senha deve conter ao menos uma letra maiúscula.')),
            (r'[a-z]', _('A senha deve conter ao menos uma letra minúscula.')),
            (r'\d', _('A senha deve conter ao menos um número.')),
            (r'[^A-Za-z0-9]', _('A senha deve conter ao menos um caractere especial.')),
        )
        errors = [message for pattern, message in requirements if not re.search(pattern, password)]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _('Use letras maiúsculas e minúsculas, número e caractere especial.')
