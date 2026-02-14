import os
from walter.bot_instance import bot

def main():
    token = os.getenv("WALTER_BOT_TOKEN")
    if not token:
        raise SystemExit("Set WALTER_BOT_TOKEN in your environment.")
    bot.run(token)

if __name__ == "__main__":
    main()
