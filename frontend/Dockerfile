# frontend/Dockerfile
# Next.js 15 (App Router) — multi-stage build using the "standalone" output
# (see next.config.ts: output: "standalone").

# ---- deps: install dependencies with lockfile ------------------------------
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
# NOTE: package-lock.json is currently out of sync with package.json
# (missing @emnapi/core@1.11.3 / @emnapi/runtime@1.11.3 resolutions), so
# `npm ci` fails with EUSAGE. Using `npm install` here lets npm repair the
# lockfile during the build. Regenerate package-lock.json locally with
# `npm install` and commit it, then switch this back to `npm ci` for
# fully reproducible builds.
RUN npm install

# ---- builder: build the Next.js app ----------------------------------------
FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Public build-time API URL baked into the client bundle. Must include the
# "/api" prefix used by the FastAPI router (see frontend/src/lib/api.ts).
# Override at build time with: --build-arg NEXT_PUBLIC_API_URL=https://api.example.com/api
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ---- runner: minimal production image --------------------------------------
FROM node:20-slim AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN groupadd --system --gid 1001 nodejs \
    && useradd --system --uid 1001 --gid nodejs nextjs

# Standalone output: minimal server + only the deps it actually needs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', r => process.exit(r.statusCode < 500 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "server.js"]
