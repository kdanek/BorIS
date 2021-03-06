'''
Created on 1.10.2011

@author: xaralis
'''
from django import forms

from boris.clients.models import ClientNote


class ReadOnlyWidget(forms.Widget):
    def __init__(self, original_value, display_value):
        self.original_value = original_value
        self.display_value = display_value
        super(ReadOnlyWidget, self).__init__()

    def _has_changed(self, initial, data):
        return False

    def render(self, name, value, attrs=None):
        if self.display_value is not None:
            return unicode(self.display_value)
        return unicode(self.original_value)

    def value_from_datadict(self, data, files, name):
        return self.original_value


DATE_FORMATS = (
    '%d.%m.%Y',
)
TIME_FORMATS = (
    '%H:%M:%S',
    '%H:%M',
)


class ClientNoteForm(forms.ModelForm):
    datetime = forms.SplitDateTimeField(input_date_formats=DATE_FORMATS,
                                        input_time_formats=TIME_FORMATS)

    class Meta:
        model = ClientNote
        fields = ('datetime', 'text', 'client')

