FROM alpine:3.21 AS build
RUN apk add --update npm
RUN apk add git curl bash apache2 python3 patch
RUN mkdir -p /usr/local/seal
WORKDIR /usr/local/seal
COPY configuration.toml .
COPY script.py .
COPY build_deploy.sh .
RUN chmod +x build_deploy.sh
RUN curl -fsSL https://bun.sh/install | bash
RUN git clone https://github.com/alleonhardt/algo-learn.git
COPY httpd.conf /etc/apache2/httpd.conf
RUN rm /var/www/localhost/htdocs/index.html
CMD ["sh","-c","python3 script.py & /usr/sbin/httpd -D FOREGROUND"]
