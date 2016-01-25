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
    job_id = wtforms.HiddenField("job_id")
    accepted = wtforms.BooleanField("accepted")


def job_acceptance_form_factory(jobs):
    default = [{'job_id': job['id']} for job in jobs]

    class JobAcceptanceForm(wtforms.Form):
        jobs = wtforms.FieldList(
            wtforms.FormField(SingleJobAcceptanceForm),
            default=default,
            min_entries=len(default),
            max_entries=len(default)
        )

        def get_form(self, job_id):
            for form in self.jobs:
                return form

    return JobAcceptanceForm
