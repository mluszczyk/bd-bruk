import wtforms


class NewOrderForm(wtforms.Form):
    name = wtforms.StringField("nazwa", [wtforms.validators.Length(min=4, max=250)])
    description = wtforms.TextAreaField("opis", [wtforms.validators.Length(min=4)])
    client_id = wtforms.SelectField("klient", coerce=int)

    @classmethod
    def feed_with_users(cls, request, user_list):
        """Take pairs (id, name) and return NewOrderForm instance fed with users."""
        form = cls(request)
        form.client_id.choices = user_list
        return form


class EstimateOrderForm(wtforms.Form):
    expert = wtforms.SelectField("rzeczoznawca", coerce=int)

    @classmethod
    def feed_with_experts(cls, request, expert_list):
        form = cls(request)
        form.expert.choices = expert_list
        return form


class NewJobForm(wtforms.Form):
    description = wtforms.TextAreaField("opis", [wtforms.validators.Length(min=4)])
    cost = wtforms.FloatField("koszt", [wtforms.validators.NumberRange(min=0)])


class NewEstimateForm(wtforms.Form):
    jobs = wtforms.FieldList(wtforms.FormField(NewJobForm), min_entries=2)


class SingleJobAcceptanceForm(wtforms.Form):
    job_id = field1 = wtforms.IntegerField("job_id", widget=wtforms.widgets.HiddenInput())
    accepted = wtforms.BooleanField("accepted")


def job_acceptance_form_factory(related_jobs):
    default = [{'job_id': job['id']} for job in related_jobs]

    class JobAcceptanceForm(wtforms.Form):
        jobs = wtforms.FieldList(
            wtforms.FormField(SingleJobAcceptanceForm),
            default=default,
            min_entries=len(default),
            max_entries=len(default)
        )

        def get_form(self, job_id):
            """Return form related to given job_id or any form if not found."""
            for form in self.jobs:
                if form.job_id.data == job_id:
                    return form
            return next(iter(self.jobs))

        def get_safe_data(self):
            """Return data after making sure that only indices from related_jobs are used."""
            filled_data = {
                form.job_id.data: form.accepted.data
                for form in self.jobs
            }
            return [
                {'id': job['id'], 'accepted': filled_data.get(job['id'], False)}
                for job in related_jobs
            ]

    return JobAcceptanceForm


class NewCustomer(wtforms.Form):
    name = wtforms.StringField('nazwa', validators=[wtforms.validators.Length(min=4, max=250)])
    phone = wtforms.StringField('telefon', validators=[wtforms.validators.Length(min=4, max=50)])
    email = wtforms.StringField('email', validators=[wtforms.validators.Length(min=4, max=250)])
    address_data = wtforms.TextAreaField('dane_do_faktury')


class NewExpert(wtforms.Form):
    name = wtforms.StringField('nazwa', validators=[wtforms.validators.Length(min=4, max=250)])
    email = wtforms.StringField('email', validators=[wtforms.validators.Length(min=4, max=250)])
