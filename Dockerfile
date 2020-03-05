FROM python:3.8-alpine
ENV PYTHONPATH /usr/lib/python3.8/site-packages
WORKDIR /src
RUN pip install requests && apk add py3-pillow
COPY app.py /src/app.py
EXPOSE 8124
CMD python -u app.py
