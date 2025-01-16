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

# Create a temporary file for the ffmpeg input list
FFMPEG_INPUT_LIST=$(mktemp)
awk '{print "file \x27" $0 "\x27"}' "$FILTERED_IMAGES" > "$FFMPEG_INPUT_LIST"

# Create the timelapse video using filtered images
ffmpeg -f concat -safe 0 -i "$FFMPEG_INPUT_LIST" \
  -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease" \
  -r 24 \
  -c:v libx264 \
  -crf ${CRF_QUALITY} \
  -pix_fmt yuv420p \
  _timelapse_${TIMESTAMP}.mp4

# Clean up
rm "$FILTERED_IMAGES" "$FFMPEG_INPUT_LIST"