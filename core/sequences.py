from django.db import connection


def next_sequence_value(seq_name: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT nextval('{seq_name}')")
        return cursor.fetchone()[0]
