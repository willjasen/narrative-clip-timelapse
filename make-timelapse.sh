# Define parameters
WIDTH=1920
HEIGHT=1080
CRF_QUALITY=32

# Create the timelapse video using images from all subdirectories
ffmpeg -pattern_type glob -i "*.jpg" \
  -vf "scale=${WIDTH}:${HEIGHT}:force_original_aspect_ratio=decrease,pad=${WIDTH}:${HEIGHT}:(ow-iw)/2:(oh-ih)/2" \
  -r 24 \
  -c:v libx264 \
  -crf ${CRF_QUALITY} \
  -pix_fmt yuv420p \
  _timelapse.mp4