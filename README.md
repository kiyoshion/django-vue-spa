# Django REST Framework on Docker

## Usage

1. Make .env
2. CMD

### For development
```bash
cd django-rest-api
docker-compose up
```

### For production
```bash
cd django-rest-api
docker-compose -f docker-compose.prod.yml up
```

## djoser

[djoser](https://djoser.readthedocs.io/en/latest/base_endpoints.html)

|action|method|url|prams|
|---|---|---|---|
|Register user|POST|auth/users/|'email=hoge@hoge.com&username=hoge&password=mogemoge'|
|Login|POST|auth/token/login/|'email=hoge@hoge.com&password=mogemoge'|
|Me|GET|auth/users/me/|'Authorization: Token b704c9fc3655635646356ac2950269f352ea1139'|
|Logout|POST|auth/token/logout/|'Authorization: Token b704c9fc3655635646356ac2950269f352ea1139'|
