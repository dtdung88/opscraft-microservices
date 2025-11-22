FROM nginx:1.25-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Create required directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run && \
    chown -R appuser:appgroup /var/cache/nginx /var/log/nginx /var/run && \
    chmod -R 755 /var/cache/nginx /var/log/nginx

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY proxy_params /etc/nginx/proxy_params

# Validate nginx config
RUN nginx -t

# Use unprivileged port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --spider http://localhost:8080/health || exit 1

# Note: nginx master process needs to run as root for ports < 1024
# For non-root, use port 8080 instead of 80
USER appuser

CMD ["nginx", "-g", "daemon off;"]