FROM python:3.7.2-alpine

RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev

RUN addgroup -S jet && adduser -S -G jet jet
RUN pip install jet_bridge==0.0.2
RUN pip install psycopg2
RUN apk --purge del .build-deps

USER jet

CMD ["jet_bridge"]

EXPOSE 8888
