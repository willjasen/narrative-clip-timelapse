# Define parameters
WIDTH=1920
HEIGHT=1080
CRF_QUALITY=32
GLOB="2016/05/26/*.jpg"

# Get the current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Filter images with aspect ratio over 0.85
FILTERED_IMAGES=$(mktemp)
for img in 2016/05/26/*.jpg; do
  # Skip images that have already been checked
  if [[ -f "${img}.checked" ]]; then
    echo "Skipping already checked $img"
    echo "$(realpath "$img")" >> "$FILTERED_IMAGES"
    continue
  fi

  ASPECT_RATIO=$(identify -format "%[fx:w/h]" "$img")
  if (( $(echo "$ASPECT_RATIO <= 0.85" | bc -l) )); then
    echo "Including $img with aspect ratio $ASPECT_RATIO"
    echo "$(realpath "$img")" >> "$FILTERED_IMAGES"
    touch "${img}.checked"
  else
    echo "Excluding $img with aspect ratio $ASPECT_RATIO"
  fi
done

# Create a temporary file for the ffmpeg input list and subtitles
FFMPEG_INPUT_LIST=$(mktemp)
SUBTITLES_FILE=$(mktemp).srt
FRAME_DURATION_MS=42  # 1/24 second in milliseconds

awk '{print "file \x27" $0 "\x27"}' "$FILTERED_IMAGES" > "$FFMPEG_INPUT_LIST"

# Generate subtitles from timestamps
START_TIME_MS=0
INDEX=1
while read -r img; do
  FILENAME=$(basename "$img" .jpg)
  UTC_TIMESTAMP=$(echo "$FILENAME" | sed 's/_/ /g')
  EST_TIMESTAMP=$(date -j -f "%Y%m%d %H%M%S" -v-4H "$UTC_TIMESTAMP" +"%Y-%m-%d %-I:%M:%S %p" 2>/dev/null)
  if date -j -f "%Y%m%d %H%M%S" -v-4H "$UTC_TIMESTAMP" 2>/dev/null | grep -q "EDT"; then
    EST_TIMESTAMP=$(date -j -f "%Y%m%d %H%M%S" -v-5H "$UTC_TIMESTAMP" +"%Y-%m-%d %-I:%M:%S %p" 2>/dev/null)
  fi
  EST_TIMESTAMP=$(echo "$EST_TIMESTAMP" | sed 's/ 000//')
  END_TIME_MS=$((START_TIME_MS + FRAME_DURATION_MS))
  printf "%d\n%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n%s\n\n" \
    "$INDEX" \
    $((START_TIME_MS/3600000)) $(((START_TIME_MS%3600000)/60000)) $(((START_TIME_MS%60000)/1000)) $((START_TIME_MS%1000)) \
    $((END_TIME_MS/3600000)) $(((END_TIME_MS%3600000)/60000)) $(((END_TIME_MS%60000)/1000)) $((END_TIME_MS%1000)) \
    "$EST_TIMESTAMP" >> "$SUBTITLES_FILE"
  START_TIME_MS=$END_TIME_MS
  INDEX=$((INDEX + 1))
done < "$FILTERED_IMAGES"

# Create the timelapse video using filtered images and add subtitles
ffmpeg -f concat -safe 0 -i "$FFMPEG_INPUT_LIST" \
  -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,subtitles=${SUBTITLES_FILE}" \
  -r 24 \
  -c:v libx264 \
  -crf ${CRF_QUALITY} \
  -pix_fmt yuv420p \
  timelapses/timelapse_${TIMESTAMP}.mp4

# Clean up
rm "$FILTERED_IMAGES" "$FFMPEG_INPUT_LIST" "$SUBTITLES_FILE"