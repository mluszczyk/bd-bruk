import psycopg2
import psycopg2.extras

connection = psycopg2.connect("dbname=michal")


class NotFound(Exception):
    pass


def select_wrapper(query_string, data=None):
    def f():
        with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query_string, data)
            yield from cur
    return f


# zamówienia, do których należy znaleźć bądź stworzyć kosztorys
oczekujace_zamowienia = select_wrapper("""
    SELECT id, nazwa FROM zamowienie
    WHERE kosztorys_id IS NULL AND NOT EXISTS (
        SELECT * FROM zlecenie_kosztorysu WHERE zamowienie_id = zamowienie.id
    )
""")

# zamówienia, czekające na kosztorys od rzeczoznawcy
zlecone_kosztorysy = select_wrapper("""
    SELECT zamowienie.id AS id, nazwa FROM zamowienie
    INNER JOIN zlecenie_kosztorysu ON (zamowienie_id = zamowienie.id)
    WHERE kosztorys_id IS NULL
""")

# zamówienia, które czekają na zatwierdzenie kosztorysu przez klienta
kosztorysy_do_zatwierdzenia = select_wrapper("""
    SELECT id, nazwa FROM zamowienie
    WHERE kosztorys_id IS NOT NULL AND NOT EXISTS (
        SELECT * FROM zlecenie WHERE zamowienie_id = zamowienie.id
    )
""")

# zamówienia, na podstawie których zostało sporządzone zlecenie, jednak nie
# jest jeszcze zaakceptowane
zlecenia_do_zatwierdzenia = select_wrapper("""
    SELECT zamowienie.id AS id, nazwa FROM zamowienie
    INNER JOIN zlecenie ON (zamowienie.id = zamowienie_id)
    WHERE zaakceptowane_przez_klienta = false
""")

users = select_wrapper("""
    SELECT id, nazwa FROM klient ORDER BY nazwa
""")


def save_order(name, description, client_id):
    with connection.cursor() as cur:
        cur.execute("""
            INSERT INTO zamowienie (nazwa, opis, klient_id, czas_zlozenia)
            VALUES (%s, %s, %s, now())
        """, (name, description, client_id))
    connection.commit()


def get_order_details(order_id):
    results = list(select_wrapper("""
        SELECT zamowienie.id AS id, zamowienie.nazwa AS nazwa, opis,
        klient.id AS klient_id, klient.nazwa AS nazwa_klienta, dane_do_faktury,
        email, telefon
        FROM zamowienie LEFT JOIN klient ON (klient.id = klient_id)
        WHERE zamowienie.id = %s
        LIMIT 1
    """, (order_id,))())
    if not results:
        raise NotFound
    else:
        return results[0]

