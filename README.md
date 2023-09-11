# Тестовое задание 3

- _docker-compose.yml_
```
environment:
      - POSTGRES_USER=<postgres_user>
      - POSTGRES_PASSWORD=<postgres_password>
      - POSTGRES_DB=<postgres_db>
```
- _.env_
```
DATABASE_URL=postgresql+asyncpg://<postgres_user>:<postgres_password>@database/<postgres_db>
JWT_SECRET_KEY=<secret_key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
EMAIL_HUNTER_API_KEY=<email_hunter_api_key>
```

### How to run

```
git clone git@github.com:dmitriy-lar/test-task-3.git
```

```
cd test-task-3/
```

```
docker compose up -d
```

```
localhost:8008
```
