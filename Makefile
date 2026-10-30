up:
	docker compose up -d --build
migrate:	
	docker compose exec web python manage.py migrate
seed:
	docker compese exec web python manage.py load_cities
	docker compose exec web python manage.py load_stations
test:
	docker compose exec web pytest -q
	