FROM python:3.10-bullseye

WORKDIR /

RUN apt-get update && \
    apt-get install -y gstreamer1.0-libav libnss3-tools libatk-bridge2.0-0 libcups2-dev libxkbcommon-x11-0 libxcomposite-dev libxrandr2 libgbm-dev libgtk-3-0 --fix-missing && \
    git clone https://github.com/SAGIRI-kawaii/sagiri-bot.git && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install poetry && \
    cd sagiri-bot && \
    poetry config installer.max-workers 10 && \
    poetry install

VOLUME /sagiri-bot/log

VOLUME /sagiri-bot/config

WORKDIR sagiri-bot

ENTRYPOINT ["poetry", "run", "python", "main.py"]
