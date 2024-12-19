from django.forms import SelectMultiple


class Select2SlideCheckboxWidget(SelectMultiple):
    class Media:
        css = {
            "all": (
                "https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css",
            )
        }
        js = (
            "https://code.jquery.com/jquery-3.7.1.min.js",
            "https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js",
        )
