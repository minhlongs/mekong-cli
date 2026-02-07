export BRIDGE_URL="https://bush-permit-assumptions-velvet.trycloudflare.com"
echo "$BRIDGE_URL" | CLOUDFLARE_API_TOKEN="ZGmz0rgZp4l8q8YYp8Qo9nDpu-rJbbg0QnxCkWVu" npx wrangler secret put BRIDGE_URL --force
