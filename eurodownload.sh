#!/bin/bash
# it is important for the above line to be bash and not sh

. ~/venv/eht-met-forecast/bin/activate
cd ~/github/eht-met-forecast

rm tau225.txt
wget https://vlbimon1.science.ru.nl/img/plots/tau225.txt
python scripts/copy-to-timpstamped-name.py tau225.txt
