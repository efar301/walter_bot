FROM astral/uv:python3.12-bookworm-slim

WORKDIR /bot

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . . 

CMD ["uv", "run", "run_bot.py"]

