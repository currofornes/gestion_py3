from django import forms

class DatePickerInput(forms.DateInput):
    template_name = 'widgets/datepicker.html'

    class Media:
        css = {
            'all': ('plugins/datepicker/datepicker3.css')
        }
        js = ('plugins/datepicker/bootstrap-datepicker.js', 'plugins/datepicker/locales/bootstrap-datepicker.es.min.js')

class ClockPickerInput(forms.TimeInput):
    template_name = 'widgets/clockpicker.html'

