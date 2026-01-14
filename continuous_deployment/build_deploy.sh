mkdir -p /var/www/localhost/htdocs$TARGET
PUBLIC_BASE_PATH=$TARGET /root/.bun/bin/bun install
PUBLIC_BASE_PATH=$TARGET /root/.bun/bin/bun run build
cp -r packages/svelte-front-end/build/* /var/www/localhost/htdocs$TARGET
RES=$(pwd)
cd .. && rm -rf $RES
