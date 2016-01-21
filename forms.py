from wtforms import Form, StringField, SelectField, TextAreaField, validators


class NewOrderForm(Form):
    name = StringField("nazwa", [validators.Length(min=4, max=250)])
    description = TextAreaField("opis", [validators.Length(min=4)])
    client_id = SelectField("klient", coerce=int)

    @classmethod
    def feed_with_users(cls, request, user_list):
        """Take pairs (id, name) and return NewOrderForm instance fed with users."""
        form = cls(request)
        form.client_id.choices = user_list
        return form
