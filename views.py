from flask import Flask, render_template, request, redirect
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


if __name__ == "__main__":
    app.debug = True
    app.run()
