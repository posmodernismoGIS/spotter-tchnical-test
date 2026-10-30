import csv
from decimal import Decimal
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from fuel.models import FuelStation

class Command(BaseCommand):
    help = "command to load geocoded fuel stations into Postgis"
    
    def add_arguments(self, parser):
        parser.add_argument("--path", default="data/fuel_stations_geocoded.csv")
        
    @transaction.atomic
    def handle(self, *args, **options):
        FuelStation.objects.all().delete()
        with open(options["path"], encoding="utf-8") as f:
            stations = [FuelStation(opis_id=r["opis_id"], name=r["name"], address=r["address"],
                                    city=r["city"], state=r["state"], price=Decimal(r["price"]),
                                    location=Point(float(r["lon"]), float(r["lat"]), srid=4326))
                        for r in csv.DictReader(f)]
        FuelStation.objects.bulk_create(stations, batch_size=2000)
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(stations)} stations"))