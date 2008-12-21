from django.db.models.fields import URLField
import validators

class Safe_URLField(URLField):
    def __init__(self, badware_check=True, **kwargs):
        # TODO: Wait till model-validation is checked in.
        # Currently field validation doesn't work.
        if badware_check:
            kwargs.setdefault('validator_list', []).append(validators.isBadwareURL)
        self.badware_check = badware_check
        super(Safe_URLField, self).__init__(**kwargs)

    def get_internal_type(self):
        return "CharField"

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.URLField, 'verify_exists': self.verify_exists, }
        defaults.update(kwargs)
        return super(Safe_URLField, self).formfield(**defaults)
