from flask import Flask, render_template
app = Flask(__name__)

import model


@app.route("/")
def home():
    estimates_to_send = [
        {'id': 123, 'name': 'Dom dla bezdomnych jeży'}
    ]
    context = {
        'oczekujace_zamowienia': model.oczekujace_zamowienia(),
        'kosztorysy_do_zatwierdzenia': model.kosztorysy_do_zatwierdzenia(),
        'zlecone_kosztorysy': model.zlecone_kosztorysy(),
        'zlecenia_do_zatwierdzenia': model.zlecenia_do_zatwierdzenia()
    }
    return render_template('home.html', **context)


if __name__ == "__main__":
    app.debug = True
    app.run()
