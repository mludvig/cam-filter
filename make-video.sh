ffmpeg -framerate 30 -i tmp/%06d-capture.jpg -c:v libx264 -profile:v high -crf 25 -pix_fmt yuv420p $1
