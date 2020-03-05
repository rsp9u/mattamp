FROM python:3.7-alpine
ENV PYTHONPATH /usr/lib/python3.7/site-packages
WORKDIR /src
RUN pip install requests && apk add py3-pillow
COPY app.py /src/app.py
EXPOSE 8124
CMD python -u app.py
