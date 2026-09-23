# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS dependencies
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM dependencies AS build
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=${BACKEND_URL} \
    NEXT_OUTPUT=standalone
COPY . .
RUN npm run build

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=6 \
    CMD node -e "fetch('http://127.0.0.1:3000', {signal: AbortSignal.timeout(4000)}).then(r => {if (!r.ok) process.exit(1)}).catch(() => process.exit(1))"
CMD ["node", "server.js"]
