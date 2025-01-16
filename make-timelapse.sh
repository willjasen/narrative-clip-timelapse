# Define parameters
WIDTH=1920
HEIGHT=1080
CRF_QUALITY=32
GLOB="2016/05/26/*.jpg"

# Get the current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create the timelapse video using images from all subdirectories
ffmpeg -pattern_type glob -i "2016/05/26/*.jpg" \
  -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,pad=${WIDTH}:${HEIGHT}:(ow-iw)/2:(oh-ih)/2" \
  -r 24 \
  -c:v libx264 \
  -crf ${CRF_QUALITY} \
  -pix_fmt yuv420p \
  _timelapse_${TIMESTAMP}.mp4