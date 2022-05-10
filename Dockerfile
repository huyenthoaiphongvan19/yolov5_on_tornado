FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN pip install tornado
RUN pip install -r requirements.txt
RUN pip install pymongo

EXPOSE 8888

CMD [ "python","./index.py" ]

