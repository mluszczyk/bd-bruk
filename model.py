import psycopg2
import psycopg2.extras

connection = psycopg2.connect("dbname=michal")
connection.autocommit = True


class NotFound(Exception):
    pass


class DatabaseError(Exception):
    def __init__(self, original_exception=None):
        self.original_exception = original_exception

    def __str__(self):
        return str(self.original_exception) if self.original_exception is not None else "Database error"


class IntegrityError(DatabaseError):
    pass


def select_wrapper(query_string, data=None):
    def f():
        with connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query_string, data)
            yield from cur
    return f


def execute_insert(sql_string, data):
    try:
        with connection.cursor() as cur:
            cur.execute(sql_string, data)
    except psycopg2.IntegrityError as e:
        raise IntegrityError(e)
    except psycopg2.DatabaseError as e:
        raise DatabaseError from e


# zamówienia, dla których należy znaleźć bądź zamówić kosztorys
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

experts = select_wrapper("""
    SELECT id, nazwa, email FROM rzeczoznawca ORDER BY nazwa
""")

archived_orders = select_wrapper("""
    SELECT zamowienie.id AS id, nazwa FROM zamowienie
    INNER JOIN zlecenie ON (zamowienie.id = zamowienie_id)
    WHERE zaakceptowane_przez_klienta = true
    ORDER BY id
""")

customers = select_wrapper("""
    SELECT nazwa, dane_do_faktury, email, telefon
    FROM klient
    ORDER BY nazwa
""")

estimates = select_wrapper("""
    SELECT zamowienie.id AS id, nazwa
    FROM kosztorys
    LEFT JOIN zlecenie_kosztorysu ON (zlecenie_kosztorysu_id = zlecenie_kosztorysu.id)
    LEFT JOIN zamowienie ON (zamowienie_id = zamowienie.id)
    ORDER BY id
""")


def save_order(name, description, client_id):
    execute_insert("""
        INSERT INTO zamowienie (nazwa, opis, klient_id, czas_zlozenia)
        VALUES (%s, %s, %s, now())
    """, (name, description, client_id))


def create_estimate_order(order_id, expert_id):
    try:
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO zlecenie_kosztorysu (czas_zamowienia, rzeczoznawca_id, zamowienie_id)
                VALUES (now(), %s, %s)
            """, (expert_id, order_id))
        connection.commit()
    except psycopg2.IntegrityError as e:
        raise IntegrityError(e)


def save_estimate(order_id, jobs):
    try:
        connection.autocommit = False
        with connection.cursor() as cur:
            cur.execute("""
                SELECT id FROM zlecenie_kosztorysu
                WHERE zamowienie_id = %s
            """, (order_id,))
            estimate_order_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO kosztorys (czas_sporzadzenia, zlecenie_kosztorysu_id)
                VALUES (now(), %s)
                RETURNING id
            """, (estimate_order_id,))

            estimate_id = cur.fetchone()[0]

            for job in jobs:
                cur.execute("""
                    INSERT INTO praca (opis, koszt, kosztorys_id)
                    VALUES (%s, %s, %s)
                """, (job['description'], job['cost'], estimate_id))

            cur.execute("""
                UPDATE zamowienie SET kosztorys_id = %s
                WHERE id = %s
            """, (estimate_id, order_id))
        connection.commit()

    except psycopg2.Error as e:
        connection.rollback()
        raise DatabaseError(e)

    except:
        connection.rollback()
        raise

    finally:
        connection.autocommit = True


def get_order_details(order_id):
    results = list(select_wrapper("""
        SELECT zamowienie.id AS id, zamowienie.nazwa AS nazwa, opis,
        klient.id AS klient_id, klient.nazwa AS nazwa_klienta, dane_do_faktury,
        email, telefon, kosztorys_id, czas_sporzadzenia as czas_sporzadzenia_kosztorysu,
        zlecenie.id as zlecenie_id,
        zaakceptowane_przez_klienta
        FROM zamowienie LEFT JOIN klient ON (klient.id = klient_id)
        LEFT JOIN kosztorys ON (kosztorys.id = kosztorys_id)
        LEFT JOIN zlecenie ON (zamowienie.id = zlecenie.zamowienie_id)
        WHERE zamowienie.id = %s
        LIMIT 1
    """, (order_id,))())
    if not results:
        raise NotFound
    else:
        return results[0]


def get_estimate_order(order_id):
    results = list(select_wrapper("""
        SELECT czas_zamowienia, rzeczoznawca.nazwa as nazwa_rzeczoznawcy
        FROM zlecenie_kosztorysu LEFT JOIN rzeczoznawca ON (rzeczoznawca_id = rzeczoznawca.id)
        WHERE zamowienie_id = %s
    """, (order_id,))())
    if not results:
        raise NotFound
    else:
        return results[0]


def get_jobs(order_id):
    results = list(select_wrapper("""
        SELECT praca.id AS id, praca.opis, koszt, zaakceptowane
        FROM zamowienie
        LEFT JOIN praca ON (zamowienie.kosztorys_id = praca.kosztorys_id)
        LEFT JOIN zlecenie ON (zlecenie.zamowienie_id = zamowienie.id)
        LEFT JOIN akceptacja_pracy ON (praca_id = praca.id AND zlecenie_id = zlecenie.id)
        WHERE zamowienie.id = %s
    """, (order_id, ))())
    return results


def save_job_acceptance(order_id, jobs):
    connection.autocommit = False
    try:
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO zlecenie (zaakceptowane_przez_klienta, zamowienie_id)
                VALUES (%s, %s)
                RETURNING id
            """, (False, order_id))

            contract_id = cur.fetchone()[0]

            for job in jobs:
                cur.execute("""
                    INSERT INTO akceptacja_pracy (zaakceptowane, praca_id, zlecenie_id)
                    VALUES (%s, %s, %s)
                """, (job['accepted'], job['id'], contract_id))
        connection.commit()
    except psycopg2.IntegrityError as e:
        connection.rollback()
        raise IntegrityError(e)
    except:
        connection.rollback()
        raise
    finally:
        connection.autocommit = True


def accept_contract(order_id):
    try:
        with connection.cursor() as cur:
            cur.execute("""
                UPDATE zlecenie
                SET zaakceptowane_przez_klienta = true
                WHERE id = (SELECT id FROM zlecenie WHERE zamowienie_id = %s)
            """, (order_id, ))
    except psycopg2.DatabaseError as e:
        raise DatabaseError from e


def save_customer(name, email, phone, address_data):
    execute_insert("""
        INSERT INTO klient (nazwa, email, telefon, dane_do_faktury)
        VALUES (%s, %s, %s, %s)
    """, (name, email, phone, address_data))


def save_expert(name, email):
    execute_insert("""
        INSERT INTO rzeczoznawca (nazwa, email) VALUES (%s, %s)
    """, (name, email))


def assign_estimate(order_id, model_order_id):
    execute_insert("""
        UPDATE zamowienie
        SET kosztorys_id = (SELECT kosztorys_id FROM zamowienie WHERE id = %s)
        WHERE kosztorys_id IS NULL and id = %s
    """, (model_order_id, order_id))
