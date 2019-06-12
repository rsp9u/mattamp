mattamp
=======

# Description

Enables big emoji for Mattermost like [slamp](https://github.com/16g/slamp).

# Prerequisite

* Python3
* reqeusts
* Enabled the following settings in Mattermost
  - Custom Emoji
  - Custom Slash Commands
  - Personal Access Tokens
* An admin's personal access token

# Getting started

1. Create `.env` file from `.env.template`
2. Run server
   ```
   $ source .env
   $ python3 app.py
   ```
3. Add custom emojis to Mattermost
4. Add a custom slash command
5. Type slash command on Mattermost like this
   ```
   /stamp :custom_emoji:
   ```

# Notes

* First time only, emoji is displayed as an attached file and the posting user becomes admin user.
  - After the second time, emoji is displayed as an image link and the posting user name is impersonated.
  - If you delete the first time post, the image link will be unavailable after Mattermost clean up process.
    - So, you should not delete the first time post.

* If `IMPERSONATE` option is true, emoji message is posted as user post completly.
* If `IMPERSONATE` option is false, emoji message is displayed as a return of slash command (added `BOT`).

* If `IMPERSONATE` option is true, this server will create and store as a local file.
  - Use the option internally.
