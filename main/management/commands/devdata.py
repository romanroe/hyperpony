import djclick as click

from main.models import AppUser


def create_admin():
    user = AppUser(email="admin@d.com", username="admin")
    user.is_superuser = True
    user.is_staff = True
    user.set_password("pw")
    user.save()
    return user


@click.command()
def command():
    click.secho("Inserting DevData", bg="green")
    create_admin()
