ARG AGENT_IMAGE
FROM ${AGENT_IMAGE}
USER root
# node/npm：TypeScript 的編譯和測試；php-cli：agent 可以跑 php -l、讀懂並試跑 legacy/php 的片段
RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm php-cli \
 && rm -rf /var/lib/apt/lists/*
USER agent
