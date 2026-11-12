#!/bin/bash
set -u
app_dir="$(cd "$(dirname "$0")/.." && pwd)"
results_dir="$HOME/Documents/PALO-BlueprintBench-Agent/reviews"
mkdir -p "$results_dir"
run_id="$(date +%Y%m%d-%H%M%S)-$RANDOM"
run_dir="$results_dir/calibration-$run_id"
printf 'PALO BlueprintBench internal calibration\n\nOpen LM Studio, start its local server, and load qwen3.8-27b-uncensored.\nThis runs 18 synthetic examples and can take a long time.\nThe diagnostic does not validate the benchmark or provide independent review.\n\n'
python3 "$app_dir/validation_agent/agent.py" calibrate --out "$run_dir"
run_exit=$?
if [ -f "$run_dir/calibration.html" ]; then
  /usr/bin/open "$run_dir/calibration.html"
  printf '\nReport: %s/calibration.html\n' "$run_dir"
elif [ -f "$run_dir/report.html" ]; then
  /usr/bin/open "$run_dir/report.html"
  printf '\nReview report: %s/report.html\n' "$run_dir"
else
  printf '\nNo final report was produced. Inspect progress and request files in: %s\n' "$run_dir"
fi
printf '\nExit status: %s. Press Enter to close.\n' "$run_exit"
read -r
exit "$run_exit"
