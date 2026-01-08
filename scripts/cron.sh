#!/bin/sh
set -e

SCHEDULE_CRON=${SCHEDULE_CRON:-"20 12 * * 1-5"}
TIMEZONE=${TIMEZONE:-"Europe/Warsaw"}

export TZ=$TIMEZONE

mkdir -p /var/log/cron

cat <<CRON > /etc/cron.d/charon
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/bin:/bin
${SCHEDULE_CRON} cd /app/backend && python -m app.jobs.runner >> /var/log/cron/cron.log 2>&1
CRON

chmod 0644 /etc/cron.d/charon
crontab /etc/cron.d/charon

cron -f
