import sys
import time
import os
import os.path

from tqdm.contrib.slack import trange

from eht_met_forecast import slack_utils


if os.getenv('SLACK_QUIET'):
    exit(0)

token, channel_id = slack_utils.get_slack_token('eht', 'ehtobs_bots')

name = sys.argv[1]

# wait up to 2 hours for this file to appear
start = time.time()
while time.time() < start + 7200:
    if os.path.exists(name):
        break

with open(name) as fd:
    count = len(fd.read().splitlines())

tqdm_bar = trange(210, initial=count, token=token, channel=channel_id)
#tqdm_bar = trange(210, initial=count)
tqdm_bar.set_description('GFS download')
last = count

while True:
    with open(name) as fd:
        count = len(fd.read().splitlines())
    if count != last:
        tqdm_bar.update(count - last)
        last = count
    if count == 210:
        break
    time.sleep(60)

tqdm_bar.close()
