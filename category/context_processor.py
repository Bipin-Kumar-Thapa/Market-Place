from .models import Category


def menu_links(request):
    links = Category.objects.all().filter(status=True)
    return dict(links=links)
