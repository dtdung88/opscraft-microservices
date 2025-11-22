FROM nginx:alpine

# Create a non-root user
RUN addgroup -S app && adduser -S app -G app

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose application port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --spider http://localhost:8000/ || exit 1

# Switch to non-root user
USER app

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
