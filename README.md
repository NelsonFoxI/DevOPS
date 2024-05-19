Рекомендуется использовать Ubuntu 22.04


Поля для файла '.env':

    ```plaintext
    TOKEN=
    RM_HOST=
    RM_PORT=22
    RM_USER=
    RM_PASSWORD=
    DB_USER=
    DB_PASSWORD=
    DB_HOST=
    DB_PORT=5432
    DB_DATABASE=tg_bot
    DB_REPL_USER=
    DB_REPL_PASSWORD=
    DB_REPL_HOST=repl_db_host
    DB_REPL_PORT=5432
    ```

Запустите проект с помощью Docker Compose:

    ```bash
    docker-compose up -d --build
    ```

