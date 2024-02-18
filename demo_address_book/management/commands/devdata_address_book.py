import csv
from pathlib import Path
from typing import cast

import djclick as click

from demo_address_book.models import Person


@click.command()
def command():
    with open(Path(__file__).parent / "100-contacts.csv", "r") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            r = cast(dict[str, str], row)
            p = Person(first_name=r["first_name"], last_name=r["last_name"])
            p.save()
