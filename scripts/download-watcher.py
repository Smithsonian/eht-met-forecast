import sys
import time
import os
import os.path

from tqdm.contrib.slack import trange

from eht_met_forecast import slack_utils


if os.getenv('SLACK_QUIET'):
    exit(0)

token, channel_id = slack_utils.get_slack_token('eht', 'ehtobs_bots')
webhook = slack_utils.get_slack_webhook('eht', 'ehtobs_bots')

fname = sys.argv[1]

# wait up to 4 hours for this file to appear
warned = False
start = time.time()
while time.time() < start + 14400:
    if os.path.exists(fname):
        break
    # but warn after 2 hours:
    if not warned and time.time() > start + 7200:
        slack_utils.slack_message('Warning: GFS download has not yet started, still trying', webhook)
        warned = True
else:
    slack_utils.slack_message('Error: GFS download has not yet started, giving up', webhook)

with open(fname) as fd:
    count = len(fd.read().splitlines())

tqdm_bar = trange(210, initial=count, token=token, channel=channel_id)
#tqdm_bar = trange(210, initial=count)
tqdm_bar.set_description('GFS download')
last = count

while True:
    with open(fname) as fd:
        count = len(fd.read().splitlines())
    if count != last:
        tqdm_bar.update(count - last)
        last = count
    if count == 210:
        break
    time.sleep(60)

tqdm_bar.close()
