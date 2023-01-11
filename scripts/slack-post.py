import sys

import eht_met_forecast.slack_utils


slack = sys.argv[1]
channel = sys.argv[2]
message = ' '.join(sys.argv[3:])

webhook = eht_met_forecast.slack_utils.get_slack_webhook(slack, channel)

eht_met_forecast.slack_utils.slack_message(message, webhook)
