FROM nginx:1.20.2-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY app_nginx.conf /etc/nginx/conf.d
COPY nginx.conf /etc/nginx/nginx.conf