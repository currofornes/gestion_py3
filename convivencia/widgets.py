from django import forms

class DatePickerInput(forms.DateInput):
    template_name = 'widgets/datepicker.html'

    class Media:
        css = {
            'all': ('css/plugins/datapicker/datepicker3.css')
        }
        js = ('js/plugins/datapicker/bootstrap-datepicker.js', 'js/plugins/datapicker/locales/bootstrap-datepicker.es.min.js')

class ClockPickerInput(forms.TimeInput):
    template_name = 'widgets/clockpicker.html'

    class Media:
        css = {
            'all': ('css/plugins/clockpicker/clockpicker.css')
        }
        js = ('js/plugins/clockpicker/clockpicker.js')