#!/bin/bash

echo "Processing $@"
while getopts ":i:o:s:" opt; do
  case ${opt} in
    i )
      INPUT_PATH="$OPTARG"
      ;;
    s )
      SESSION="$OPTARG"
      ;;
    o )
      OUTPUT_FILE="$OPTARG"
      ;;
    \? ) echo "Usage: cmd [-i] [-s] [-o]"
      ;;
  esac
done
shift $((OPTIND -1))

TMP_DIR=$(mktemp -d -t render-video-XXXXXXXXXX)

gsutil -m cp -r "$INPUT_PATH" "$TMP_DIR"
ffmpeg -pattern_type glob -i "$TMP_DIR/$SESSION/*.jpg" "$TMP_DIR/timelapse.mp4"
gsutil -m cp "$TMP_DIR/timelapse.mp4" $OUTPUT_FILE
trap '{ rm -rf -- "$TMP_DIR"; }' EXIT
