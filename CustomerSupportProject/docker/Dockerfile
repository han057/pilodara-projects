FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY app ./app
COPY data ./data
COPY scripts/check_project.py ./scripts/check_project.py
COPY .streamlit ./.streamlit
COPY streamlit_app.py ./

RUN mkdir -p /app/chroma_db \
    && python -m compileall -q app streamlit_app.py scripts/check_project.py

EXPOSE 8000 8501
