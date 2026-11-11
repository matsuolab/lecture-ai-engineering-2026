
FROM python:3.12-slim

# uvをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

EXPOSE 8501

CMD ["sh", "-c", "uv sync && uv run --no-sync streamlit run tools/annotate.py --server.address=0.0.0.0 --server.port=8501 --server.fileWatcherType=poll"]

