# Smart Service

Prosty watchdog internetu dla Raspberry Pi uruchamiany w Dockerze.

Jeśli urządzenie nie ma internetu przez zadany czas, kontener wykonuje reboot hosta.

## Jak to działa

Serwis wykonuje dwa testy łączności:

- próbę połączenia TCP do `SOCKET_HOST:SOCKET_PORT`
- żądanie HTTP do `HTTP_URL`

Jeśli oba testy nie przejdą, zaczyna liczyć czas awarii. Po przekroczeniu `MAX_OUTAGE_SECONDS`
uruchamia:

```bash
nsenter --target 1 --mount --uts --ipc --net --pid /sbin/reboot
```

To powoduje reboot Raspberry Pi, a nie tylko restart kontenera.

## Pliki

- `app/main.py` - pętla watchdog
- `app/config.py` - konfiguracja z env
- `Dockerfile` - obraz pod ARM i x86
- `docker-compose.yml` - uruchomienie z uprawnieniami hosta

## Konfiguracja

1. Skopiuj plik env:

```bash
cp env.example .env
```

2. Najważniejsze opcje:

- `CHECK_INTERVAL_SECONDS=30` - co ile sekund sprawdzać internet
- `MAX_OUTAGE_SECONDS=600` - po ilu sekundach bez internetu wykonać reboot
- `REBOOT_COMMAND=...` - domyślnie reboot hosta przez `nsenter`

## Lokalny build

```bash
docker build --target runtime -t docker.io/kennydaktyl/smart-service:latest .
```

## Build pod Raspberry Pi

Jeżeli celujesz w Raspberry Pi Zero 2 W, najbezpieczniejszy target to `linux/arm/v7`.

```bash
docker buildx build --platform linux/arm/v7 --target runtime -t docker.io/kennydaktyl/smart-service:latest --push .
```

Jeżeli to jednak starsze Raspberry Pi Zero W, użyj `linux/arm/v6`.

```bash
docker buildx build --platform linux/arm/v6 --target runtime -t docker.io/kennydaktyl/smart-service:latest --push .
```

## Uruchomienie na Raspberry Pi

```bash
docker compose up -d
```

Kontener wymaga:

- `privileged: true`
- `network_mode: host`
- `pid: host`

Bez tego nie zrestartuje hosta.

## Logi

```bash
docker logs -f smart-service
```

## Ważne

Przed wdrożeniem sprawdź ręcznie, czy reboot z kontenera działa:

```bash
docker compose run --rm smart-service sh -lc 'nsenter --target 1 --mount --uts --ipc --net --pid /sbin/reboot'
```

To polecenie zrestartuje Raspberry Pi natychmiast.
