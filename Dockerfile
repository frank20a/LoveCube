FROM python:3.10.13-bookworm

COPY ./server/requirements.txt ./app/requirements.txt

WORKDIR /app

RUN pip install --upgrade -r requirements.txt

COPY ./server .

ENV ONLINE=1

EXPOSE 5000

ENTRYPOINT [ "python3" ]

CMD ["app_.py"]