FROM mcr.microsoft.com/playwright:v1.41.1-jammy

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip

RUN curl -fsSL https://bun.sh/install | bash


# Copy client and admin code
COPY ./yellow-client /app/yellow-client
COPY ./yellow-admin /app/yellow-admin


RUN cd /app/yellow-client && ~/.bun/bin/bun i --frozen-lockfile

CMD ["npx", "playwright", "test", "/app/yellow-client/src/modules/org.libersoft.messages/tests/e2e/everything.test.ts", "--reporter=line,github"]