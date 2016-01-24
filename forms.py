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


class EstimateOrderForm(Form):
    expert = SelectField("rzeczoznawca", coerce=int)

    @classmethod
    def feed_with_experts(cls, request, expert_list):
        form = cls(request)
        form.expert.choices = expert_list
        return form