##############################
#        BUILDER STAGE       #
##############################
FROM node:20-alpine AS builder

WORKDIR /app

# Install only production dependencies
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy only required source files
COPY src ./src
COPY public ./public

# Build the application
RUN npm run build


##############################
#     PRODUCTION STAGE       #
##############################
FROM nginx:alpine

# Create non-root user
RUN addgroup -S app && adduser -S app -G app

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Fix permissions for non-root user
RUN chown -R app:app /usr/share/nginx/html

# Switch to non-root
USER app

EXPOSE 80

# --- HEALTHCHECK ---
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
