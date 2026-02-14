#!/bin/bash
cd /var/www/fantasy-telegram

# Проверяем есть ли изменения
if [[ -n $(git status --porcelain) ]]; then
    git add -A
    git commit -m "auto: $(date '+%Y-%m-%d %H:%M')"
    git push origin main
fi
