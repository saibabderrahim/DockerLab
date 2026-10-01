FROM nginx:1.27-alpine

# Only the static site is baked in. nginx.conf is injected by the stack as a
# Docker config so you can change proxy behaviour WITHOUT rebuilding this image.
COPY html/ /usr/share/nginx/html/

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD wget -q -O- http://localhost/ >/dev/null || exit 1