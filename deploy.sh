#!/bin/bash
echo "Iniciando deploy otimizado..."
docker compose down -v
find . -name "__pycache__" -type d -exec rm -rf {} +
docker compose up -d --build
echo "Aguardando o banco e o backend iniciarem..."
sleep 5
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
echo "Deploy concluído com sucesso!"
