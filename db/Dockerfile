FROM postgres:latest
ARG DB_REPL_USER
ARG DB_REPL_PASSWORD
ARG DB_DATABASE
ARG DB_PORT
COPY init.sql /init.sql
RUN mkdir -p /etc/postgresql/
RUN mkdir -p /oracle/pg_data/archive/
RUN chown postgres:postgres /oracle/pg_data/archive/
RUN apt-get update && apt-get install gettext-base
RUN envsubst '${DB_REPL_USER} ${DB_REPL_PASSWORD} ${DB_DATABASE}' </init.sql> /docker-entrypoint-initdb.d/init.sql
RUN echo "listen_addresses = '*'" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "port = ${DB_PORT}" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "archive_mode = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "archive_command = 'cp %p /oracle/pg_data/archive/%f'" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "max_wal_senders=10" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "wal_level=replica" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "wal_log_hints = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "hot_standby=on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "max_replication_slots=10" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "hot_standby_feedback=on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "log_replication_commands=on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "log_destination = stderr" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "logging_collector = on" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "log_directory = '/var/log/postgresql/'" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "log_filename = 'postgresql.log'" >> /usr/share/postgresql/postgresql.conf.sample
