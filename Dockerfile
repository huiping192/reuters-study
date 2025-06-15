FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app/ .
COPY ./migrations/ ./migrations/
RUN mkdir -p /app/instance && chmod 777 /app/instance
ENV FLASK_APP=app.py
EXPOSE 5000

# 创建启动脚本
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
