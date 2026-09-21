from organizations.models import Organization


def default_organization():
    """Organización a la que se asignan los datos que entran sin usuario (web pública)."""
    return Organization.objects.order_by('id').first()
