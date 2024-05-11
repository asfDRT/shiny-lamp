FROM postgres:15

ARG DB_REPL_USER
ARG DB_REPL_PASSWORD

ENV DB_REPL_USER ${DB_REPL_USER}
ENV DB_REPL_PASSWORD ${DB_REPL_PASSWORD}

RUN apt-get update && apt-get install -y gettext-base

RUN echo ${DB_REPL_USER}
RUN echo ${DB_REPL_PASSWORD}


COPY init.sql /init.sql
RUN cat /init.sql

RUN envsubst < /init.sql > /docker-entrypoint-initdb.d/init.sql.temp && \
     mv /docker-entrypoint-initdb.d/init.sql.temp /docker-entrypoint-initdb.d/init.sql && \
     chown postgres:postgres /docker-entrypoint-initdb.d/init.sql

RUN cat /docker-entrypoint-initdb.d/init.sql


CMD ["postgres"]
