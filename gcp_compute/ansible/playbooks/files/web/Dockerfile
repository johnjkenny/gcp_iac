FROM php:8.2-fpm

RUN docker-php-ext-install mysqli
RUN apt update && apt install -y nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY index.php /var/www/html/
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 755 /var/www/html
CMD service nginx start && php-fpm
