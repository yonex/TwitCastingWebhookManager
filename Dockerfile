FROM python:alpine
RUN pip install Flask requests
COPY ./ /app
WORKDIR /app
CMD ["env", "FLASK_APP=app.py", "flask", "run", "--host=0.0.0.0"]
