from flask import Flask, render_template
app = Flask(__name__)


@app.route("/")
def home():
    estimates_to_send = [
        {'id': 123, 'name': 'Dom dla bezdomnych jeży'}
    ]
    context = {
        'estimates_to_send': estimates_to_send,
    }
    return render_template('home.html', **context)


if __name__ == "__main__":
    app.run()
