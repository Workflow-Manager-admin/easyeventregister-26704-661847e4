#!/bin/bash
cd /home/kavia/workspace/code-generation/easyeventregister-26704-661847e4/easy_event_register
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

