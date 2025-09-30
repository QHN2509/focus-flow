FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip && pip install -r requirements-pinned.txt
CMD ["python", "train_classifier.py"]
