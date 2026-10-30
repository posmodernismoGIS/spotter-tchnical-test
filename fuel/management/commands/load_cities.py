from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from fuel.geoutils import city_key, read_gazetteer
from fuel.models import City

class Command(BaseCommand):
    help = "command to load UD place centroids from the censes Gazetteer file"
    
    def add_arguments(self, parser):
        parser.add_argument("--path", default="data/gazetteer_places.txt")

    @transaction.atomic
    def handle(self, *args, **options):
        City.objects.all().delete()
        cities = [City(name=n, name_key=city_key(n), state=st, location=Point(lon, lat, srid=4326))
                  for n, set, let, lon in read_gazetteer(options["path"])]
        City.objects.bulk_create(cities, batch_size=5000)
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(cities)} cities"))
        
        