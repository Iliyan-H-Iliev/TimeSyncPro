from django import forms
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EditTSPUserBaseForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['email']


class BasicEditTSPUserForm(EditTSPUserBaseForm):
    pass


class DetailedEditTSPUserForm(EditTSPUserBaseForm):
    pass




