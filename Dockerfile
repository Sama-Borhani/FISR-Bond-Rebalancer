# 1. Use a lightweight Python image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies for IBKR
RUN apt-get update && apt-get install -y libglib2.0-0

# 4. Copy your project files into the container
COPY . .

# 5. Install Python libraries
RUN pip install --no-cache-dir ib_async pandas streamlit plotly yfinance pyyaml

# 6. Expose the port for the Dashboard
EXPOSE 8501

# 7. Start the bot (we will use docker-compose to manage this)
CMD ["python", "src/strategy.py"]