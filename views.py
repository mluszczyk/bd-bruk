from flask import Flask, render_template, request, redirect, url_for
import werkzeug.exceptions

app = Flask(__name__)

import model, forms
from auth import login_required, login_factory


app.route("/login/")(login_factory(app))


@app.route("/")
@login_required(app)
def home():
    context = {
        'oczekujace_zamowienia': model.oczekujace_zamowienia(),
        'kosztorysy_do_zatwierdzenia': model.kosztorysy_do_zatwierdzenia(),
        'zlecone_kosztorysy': model.zlecone_kosztorysy(),
        'zlecenia_do_zatwierdzenia': model.zlecenia_do_zatwierdzenia()
    }
    return render_template('home.html', **context)


@app.route('/nowe_zamowienie/', methods=['POST', 'GET'])
@login_required(app)
def new_order():
    user_list = [(user['id'], user['nazwa']) for user in model.users()]
    form = forms.NewOrderForm.feed_with_users(request.form, user_list)
    if request.method == 'POST' and form.validate():
        model.save_order(form.name.data, form.description.data, form.client_id.data)
        return redirect('/')
    return render_template('new_order.html', form=form)


@app.route('/zamowienie/<int:order_id>/')
@login_required(app)
def order(order_id):
    try:
        details = model.get_order_details(order_id)
    except model.NotFound:
        raise werkzeug.exceptions.NotFound
    try:
        estimate_order = model.get_estimate_order(order_id)
    except model.NotFound:
        estimate_order = None
    jobs = model.get_jobs(order_id)
    return render_template('order.html', details=details,
                           estimate_order=estimate_order, jobs=jobs)


@app.route('/zamow_kosztorys/<int:order_id>/', methods=['GET', 'POST'])
@login_required(app)
def order_estimate(order_id):
    expert_list = [(expert['id'], expert['nazwa']) for expert in model.experts()]
    estimate_order_form = forms.EstimateOrderForm.feed_with_experts(request.form, expert_list)
    if request.method == 'POST' and estimate_order_form.validate():
        try:
            model.create_estimate_order(order_id, estimate_order_form.expert.data)
        except model.DatabaseError:
            raise werkzeug.exceptions.Forbidden("Zlecenie wykonania kosztorysu już istnieje!")
        else:
            return redirect('/')

    return render_template('estimate_order.html', order_id=order_id,
                           estimate_order_form=estimate_order_form)


@app.route('/nowy_kosztorys/<int:order_id>/', methods=['POST', 'GET'])
@login_required(app)
def new_estimate(order_id):
    estimate_form = forms.NewEstimateForm(request.form)
    if request.method == 'POST' and estimate_form.validate():
        try:
            model.save_estimate(order_id, jobs=estimate_form.jobs.data)
        except model.DatabaseError:
            raise werkzeug.exceptions.Forbidden()
        else:
            return redirect('/')

    return render_template('new_estimate.html', order_id=order_id, estimate_form=estimate_form)


@app.route('/akceptuj_prace/<int:order_id>/', methods=['POST', 'GET'])
@login_required(app)
def accept_jobs(order_id):
    try:
        jobs = model.get_jobs(order_id)
    except model.NotFound:
        raise werkzeug.exceptions.NotFound

    jobs_form = forms.job_acceptance_form_factory(jobs)(request.form)
    if request.method == 'POST' and jobs_form.validate():
        data = jobs_form.get_safe_data()
        if not any(d['accepted'] for d in data):
            try:
                model.reject_order(order_id)
            except model.DatabaseError as e:
                raise werkzeug.exceptions.Forbidden from e
        else:
            try:
                model.save_job_acceptance(order_id, data)
            except model.DatabaseError as e:
                raise werkzeug.exceptions.Forbidden from e
        return redirect(url_for('order', order_id=order_id))
    return render_template("jobs_form.html", jobs_form=jobs_form, order_id=order_id,
                           jobs=jobs)


@app.route('/akceptuj_zlecenie/<int:order_id>/')
@login_required(app)
def accept_contract(order_id):
    try:
        model.accept_contract(order_id)
    except model.DatabaseError as e:
        raise werkzeug.exceptions.NotFound from e
    else:
        return redirect('/')


@app.route('/archwium_zamowien/')
@login_required(app)
def order_archive():
    orders = model.archived_orders()
    return render_template('order_archive.html', orders=orders)


@app.route('/klienci/')
@login_required(app)
def customers():
    customers = model.customers()
    return render_template('customers.html', customers=customers)


@app.route('/nowy_klient/', methods=['POST', 'GET'])
@login_required(app)
def new_customer():
    form = forms.NewCustomer(request.form)
    if request.method == 'POST' and form.validate():
        try:
            model.save_customer(form.name.data, form.email.data,
                                form.phone.data, form.address_data.data)
        except model.DatabaseError as e:
            raise werkzeug.exceptions.Forbidden from e
        else:
            return redirect(url_for('home'))
    return render_template('new_customer.html', form=form)

@app.route('/rzeczoznawcy/')
@login_required(app)
def experts():
    experts = model.experts()
    return render_template('experts.html', experts=experts)


@app.route('/nowy_rzeczoznawca/', methods=['POST', 'GET'])
@login_required(app)
def new_expert():
    form = forms.NewExpert(request.form)
    if request.method == 'POST' and form.validate():
        try:
            model.save_expert(form.name.data, form.email.data)
        except model.DatabaseError as e:
            raise werkzeug.exceptions.Forbidden from e
        else:
            return redirect(url_for('home'))
    return render_template('new_expert.html', form=form)


@app.route('/przypisz_kosztorys/<int:order_id>/', methods=['GET', 'POST'])
@login_required(app)
def assign_estimate(order_id):
    estimate_list = model.estimates()
    form = forms.AssignEstimateForm.feed_with_orders(request.form, estimate_list)
    if request.method == 'POST' and form.validate():
        if 'preview' in request.form:
            return redirect(url_for('order', order_id=form.model_order_id.data))
        try:
            model.assign_estimate(order_id, form.model_order_id.data)
        except model.DatabaseError as e:
            raise werkzeug.exceptions.Forbidden from e
        else:
            return redirect(url_for('home'))
    return render_template('assign_estimate.html', order_id=order_id, form=form)


@app.route('/odrzuc/<int:order_id>')
@login_required(app)
def reject_order(order_id):
    model.reject_order(order_id)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.debug = True
    app.run()
