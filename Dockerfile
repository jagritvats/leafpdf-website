# leafpdf.org: static files served by nginx as a non-root user on port 8080.
# No RUN steps, so the arm64 image builds on any runner without emulation.
FROM nginxinc/nginx-unprivileged:1.28-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html/
EXPOSE 8080
