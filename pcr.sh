#!/bin/bash
export PYTHONPATH=/data/project/shared/pywikibot/stable:/data/project/shared/pywikibot/stable/scripts
cd /data/project/fireflybot2
source fireflybot2/bin/activate
./pcr_bug_bot.py &
wait
