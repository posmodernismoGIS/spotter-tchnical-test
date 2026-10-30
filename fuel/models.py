from django.contrib.gis.db import models

class City(models.Model):
    name = models.CharField(max_length=120)
    name_key = models.CharField(max_length=120)
    state = models.CharField(max_length=2)
    location = models.PointField(geography=True, srid=4326)
    
    class Meta:
        db_table = "city"
        indexes = [models.Index(fields=["name_key", "state"])]
        
        
class FuelStation(models.Model):
    opis_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=2)
    price = models.DecimalField(max_digits=6, decimal_places=3)
    location = models.PointField(geography=True, srid=4326) 
    
    class Meta:
        db_table = "fuel_station"