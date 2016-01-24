from flask import Flask, render_template, request, redirect
import werkzeug.exceptions

app = Flask(__name__)

import model, forms


@app.route("/")
def home():
    context = {
        'oczekujace_zamowienia': model.oczekujace_zamowienia(),
        'kosztorysy_do_zatwierdzenia': model.kosztorysy_do_zatwierdzenia(),
        'zlecone_kosztorysy': model.zlecone_kosztorysy(),
        'zlecenia_do_zatwierdzenia': model.zlecenia_do_zatwierdzenia()
    }
    return render_template('home.html', **context)


@app.route('/nowe_zamowienie/', methods=['POST', 'GET'])
def new_order():
    user_list = [(user['id'], user['nazwa']) for user in model.users()]
    form = forms.NewOrderForm.feed_with_users(request.form, user_list)
    if request.method == 'POST' and form.validate():
        model.save_order(form.name.data, form.description.data, form.client_id.data)
        return redirect('/')
    return render_template('new_order.html', form=form)


@app.route('/zamowienie/<int:order_id>/')
def order(order_id):
    try:
        details = model.get_order_details(order_id)
    except model.NotFound:
        raise werkzeug.exceptions.NotFound
    try:
        estimate_order = model.get_estimate_order(order_id)
    except model.NotFound:
        estimate_order = None
    return render_template('order.html', details=details,
                           estimate_order=estimate_order)


@app.route('/zamow_kosztorys/<int:order_id>/', methods=['GET', 'POST'])
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



if __name__ == "__main__":
    app.debug = True
    app.run()
