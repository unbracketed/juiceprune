#!/bin/bash
# Echo argument step - echoes back the provided message

# Get the message argument from environment variable
message="${PRUNEJUICE_ARG_MESSAGE:-No message provided}"

echo "$message"