from flask import Flask, render_template
app = Flask(__name__)

import model


@app.route("/")
def home():
    context = {
        'oczekujace_zamowienia': model.oczekujace_zamowienia(),
        'kosztorysy_do_zatwierdzenia': model.kosztorysy_do_zatwierdzenia(),
        'zlecone_kosztorysy': model.zlecone_kosztorysy(),
        'zlecenia_do_zatwierdzenia': model.zlecenia_do_zatwierdzenia()
    }
    return render_template('home.html', **context)


@app.route('/nowe_zamowienie/')
def new_order():
    return render_template('new_order.html')


if __name__ == "__main__":
    app.debug = True
    app.run()
