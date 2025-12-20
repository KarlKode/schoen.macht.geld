FROM alpine:3.20

RUN apk add --no-cache sqlite rsync

COPY backup.sh /backup.sh
RUN chmod +x /backup.sh

# Run backup every 10 minutes
CMD ["sh", "-c", "while true; do /backup.sh; sleep 600; done"]