import os
from datetime import datetime, timedelta
from pathlib import Path

import gpxpy
import gpxpy.gpx
import rawpy
import piexif

# Maximum time difference in seconds
max_time_diff = timedelta(seconds=5)

# Convert degrees to dms format
def decdeg2dms(dd):
    mult = -1 if dd < 0 else 1
    mnt,sec = divmod(abs(dd)*3600, 60)
    deg,mnt = divmod(mnt, 60)
    return mult*deg, mult*mnt, mult*sec

# Loop through all track files
for track_file in Path('./tracks').glob('*.gpx'):
    # Parse GPX file
    with track_file.open() as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Get track points from GPX file
    track_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                track_points.append(point)

    # Sort track points by time
    track_points.sort(key=lambda point: point.time)

    # Process images
    for image_file in Path('./images').glob('*.raw'):
        # Open raw image
        with rawpy.imread(image_file) as raw:
            img = raw.postprocess()

        # Get image timestamp from EXIF data
        exif_dict = piexif.load(img.info['exif'])
        img_timestamp_str = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
        img_timestamp = datetime.strptime(img_timestamp_str, '%Y:%m:%d %H:%M:%S')

        # Find nearest track point
        nearest_point = min(track_points, key=lambda point: abs(point.time - img_timestamp))

        # Check if the time difference is within the allowed maximum
        if abs(nearest_point.time - img_timestamp) <= max_time_diff:
            # Update image EXIF data with location from track point
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = decdeg2dms(nearest_point.latitude)
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = decdeg2dms(nearest_point.longitude)
            exif_bytes = piexif.dump(exif_dict)
            img.save(image_file, exif=exif_bytes)
