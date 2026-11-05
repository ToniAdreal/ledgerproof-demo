FROM python:3.12-slim
RUN useradd -m lp
WORKDIR /app
COPY engine.py server.py ./
USER lp
ENV HOST=0.0.0.0 PORT=8080
EXPOSE 8080
CMD ["python", "server.py"]
