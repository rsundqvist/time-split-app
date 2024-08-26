set -e

# Use http (instead of https) to avoid ominous certificate warnings due to self-signing. Can't use e.g.
# https://letsencrypt.org/ without a domain (which I don't want to pay for).
PERMALINK_BASE_URL="http://$(curl -q https://ipecho.net/plain)/time-split/"
export PERMALINK_BASE_URL

docker compose up --wait
