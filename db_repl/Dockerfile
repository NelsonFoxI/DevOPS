FROM postgres:latest
ARG DB_HOST
ARG DB_PORT
ARG DB_REPL_PORT
ARG DB_REPL_USER
RUN echo "listen_addresses = '*'" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "port = ${DB_REPL_PORT}" >> /usr/share/postgresql/postgresql.conf.sample
RUN echo "#!/bin/bash" > /usr/local/bin/initrep.sh
RUN echo "rm -rf /var/lib/postgresql/data/*" >> /usr/local/bin/initrep.sh
RUN echo "until pg_basebackup -h ${DB_HOST} -D /var/lib/postgresql/data -p ${DB_PORT} -U ${DB_REPL_USER} -vP -w; do" >> /usr/local/bin/initrep.sh
RUN echo " echo 'Trying again'" >> /usr/local/bin/initrep.sh
RUN echo " sleep 2" >> /usr/local/bin/initrep.sh
RUN echo "done" >> /usr/local/bin/initrep.sh
RUN echo "echo 'Starting replication'" >> /usr/local/bin/initrep.sh 
RUN echo "chown -R postgres:postgres /var/lib/postgresql/data" >> /usr/local/bin/initrep.sh
RUN echo "chmod 700 /var/lib/postgresql/data" >> /usr/local/bin/initrep.sh
RUN echo "su - postgres -c '/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data'" >> /usr/local/bin/initrep.sh
RUN chmod +x /usr/local/bin/initrep.sh
CMD ["/usr/local/bin/initrep.sh"]
