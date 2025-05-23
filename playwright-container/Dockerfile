FROM mcr.microsoft.com/playwright:v1.52.0-jammy

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip

RUN curl -fsSL https://bun.sh/install | bash


# Copy client and admin code
COPY ./yellow-client /app/yellow-client
COPY ./yellow-admin /app/yellow-admin


RUN cd /app/yellow-client && ~/.bun/bin/bun i --frozen-lockfile




CMD ["sh", "-c", "export REPORTERS=\"list\"; if [ \"$CI\" = \"true\" ]; then export REPORTERS=\"list,github\"; fi; npx --prefix /app/yellow-client playwright test /app/yellow-client/src/modules/org.libersoft.messages/tests/e2e/everything.test.ts --timeout 100000 --reporter=$REPORTERS"]