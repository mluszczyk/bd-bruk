import psycopg2
import psycopg2.extras

connection = psycopg2.connect("dbname=michal")


def select_wrapper(query_string):
    def f():
        with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query_string)
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