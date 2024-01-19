# vas3k_kicker

## Fork and deploy
- install [dokku](https://dokku.com/docs/getting-started/installation/) container
- create [dokku app](https://dokku.com/docs/deployment/application-deployment/)
- install [redis plugin](https://dokku.com/docs/getting-started/install/docker/?h=redis#plugin-installation)
- link redis to the app `dokku redis:link %your_redis_base% %your_app%`
- create your [sentry](https://sentry.io/) for monitoring (or remove it from the code)
- create your [userbot](https://docs.telethon.dev/en/stable/basic/signing-in.html) and get its api_hash and api_id. login via app/login.py to your telegram account and save a session string.
- create your [vas3k app](https://vas3k.club/apps/) and get a jwt token 
- [override variables](https://dokku.com/docs/configuration/environment-variables/): SENTRY_DSN, API_HASH, API_ID, SESSION_STRING, JWT_TOKEN
- [deploy the app](https://dokku.com/docs/deployment/application-deployment/)
