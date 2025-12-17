FROM python:3.11

WORKDIR /app

# Copy backend requirements and install dependencies
COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

# Copy backend application code
COPY . ./backend

# Create storage directories
RUN mkdir -p /app/storage/pdfs /app/storage/vectors /app/storage/exports /app/storage/processed

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]