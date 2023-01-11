import os
import json
import logging

from slack_sdk.webhook import WebhookClient
try:
    from slack_sdk.webhook.async_client import AsyncWebhookClient
except ImportError:
    AsyncWebhookClient = None


'''
NOTE: this code is also released in open source

https://api.slack.com/messaging/webhooks  # create webhook
https://tqdm.github.io/docs/contrib.slack/
https://api.slack.com/authentication/basics  # add app and get oauth token
# scroll down to Scopes, add chat.write
# get channel ID from the web interface
# hover over the bot name, click "add this app to a channel", select this channel

{
  "webhooks":
  {
    "ngeht":
    {
      "analysis-challenge-bots": "https://hooks.slack.com/services/T.../..."
    }
  },
  "tokens":
  {
    "eht":
    {
      "token": "xoxb-...",
      "channels":
      {
        "ehtobs_bots": "C..."
      }
    }
  }
}

This file has strict syntax - notice the lack of trailing commas!
You can test its syntax with

$ jq . ~/.slack-secrets
'''

LOGGER = logging.getLogger(__name__)


def load_secrets(fname='~/.slack-secrets'):
    try:
        with open(os.path.expanduser(fname), 'r') as fp:
            secrets = json.load(fp)
    except Exception as e:
        LOGGER.exception('slack secret json load from {} failed with {}'.format(fname, str(e)))
        secrets = {}
    return secrets


def get_slack_token(slack, channel):
    secrets = load_secrets()
    if 'tokens' not in secrets:
        LOGGER.exception('tokens dict not seen in secrets file')
        return None, None
    if slack in secrets['tokens']:
        if 'channels' not in secrets['tokens'][slack]:
            LOGGER.exception('slack secrets {} lacks tokens dict'.format(slack))
        elif channel in secrets['tokens'][slack]['channels']:
            d = secrets['tokens'][slack]
            return d['token'], d['channels'][channel]
        else:
            LOGGER.exception('channel {} not found in slack {} token secrets'.format(channel, slack))
    else:
        LOGGER.exception('slack {} not in secrets tokens'.format(slack))
    return None, None


def get_slack_webhook(slack, channel, async_=False):
    client = AsyncWebhookClient if async_ else WebhookClient

    env = os.getenv('SERVER_SLACK_WEBHOOK')
    if env is not None:
        return client(env)

    secrets = load_secrets()
    if 'webhooks' not in secrets:
        LOGGER.exception('webhooks dict not seen in secrets file')
        return None
    if slack not in secrets['webhooks']:
        LOGGER.exception('slack {} not in secrets webhooks'.format(slack))
        return None
    if channel in secrets['webhooks'][slack]:
        return client(secrets['webhooks'][slack][channel])
    else:
        LOGGER.exception('channel {} not found in slack {} webhooks secrets'.format(channel, slack))

    return None


def slack_message(text, webhook):
    if webhook is None:
        LOGGER.warning('not sending slack message because webhook is not configured: '+text)
        return

    if os.getenv('SLACK_QUIET'):
        print('would have sent to slack:')
        print(text)
        return

    response = webhook.send(text=text)

    if response.status_code != 200:
        LOGGER.exception('abnormal response status from slack webhook: {}'.format(response.status_code))
    elif response.body != 'ok':
        LOGGER.warning('abnormal response body from slack webhook: '+response.body)


async def async_slack_message(text, webhook):
    if webhook is None:
        LOGGER.warning('not sending slack message because webhook is not configured: '+text)
        return

    if os.getenv('SLACK_QUIET'):
        print('would have sent to slack:')
        print(text)
        return

    response = await webhook.send(text=text)

    if response.status_code != 200:
        LOGGER.exception('abnormal response status from slack webhook: {}'.format(response.status_code))
    elif response.body != 'ok':
        LOGGER.warning('abnormal response body from slack webhook: '+response.body)
