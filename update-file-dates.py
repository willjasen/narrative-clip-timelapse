import os
import time
from datetime import datetime

try:
    import pytz
except ImportError:
    print("The 'pytz' module is not installed. Please install it using 'pip install pytz'")
    exit(1)

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    print("The 'PIL' module is not installed. Please install it using 'pip install pillow'")
    exit(1)

try:
    import piexif
except ImportError:
    print("The 'piexif' module is not installed. Please install it using 'pip install piexif'")
    exit(1)

def log_change(log_file, message):
    with open(log_file, 'a') as f:
        f.write(message + '\n')

def log_exif_data(file_path, log_file):
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        if (exif_data is not None):
            exif_dict = {TAGS.get(tag): value for tag, value in exif_data.items()}
            # log_message = f"EXIF data for {file_path}: {exif_dict}"
            # log_change(log_file, log_message)
            return exif_dict
        else:
            log_message = f"No EXIF data found for {file_path}"
            log_change(log_file, log_message)
    except Exception as e:
        error_message = f"Failed to read EXIF data for {file_path}: {e}"
        print(error_message)
        log_change(log_file, error_message)
    return None

def update_exif_data(file_path, dt_eastern, log_file):
    exif_dict = log_exif_data(file_path, log_file)
    if exif_dict is None:
        return False
    try:
        exif_date = exif_dict.get('DateTimeOriginal') or exif_dict.get('DateTime')
        if exif_date:
            exif_dt = datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S')
            if exif_dt == dt_eastern:
                message = f"EXIF data for {file_path} is already in sync with {dt_eastern}"
                print(message)
                log_change(log_file, message)
                return True

        # if 'DateTime' in exif_dict:
        exif_dict['DateTime'] = dt_eastern.strftime('%Y:%m:%d %H:%M:%S')
        # if 'DateTimeOriginal' in exif_dict:
        exif_dict['DateTimeOriginal'] = dt_eastern.strftime('%Y:%m:%d %H:%M:%S')
        if 'DateTimeDigitized' in exif_dict:
            exif_dict['DateTimeDigitized'] = dt_eastern.strftime('%Y:%m:%d %H:%M:%S')
        exif_bytes = piexif.dump(exif_dict)
        image = Image.open(file_path)
        image.save(file_path, "jpeg", exif=exif_bytes)
        
        # Update file's access and modified times to match EXIF data
        timestamp = time.mktime(dt_eastern.timetuple())
        os.utime(file_path, (timestamp, timestamp))
        
        message = f"Updated EXIF data for {file_path} to {dt_eastern}"
        print(message)
        log_change(log_file, message)
        
        return True
    except Exception as e:
        error_message = f"Failed to update EXIF data for {file_path}: {e}"
        print(error_message)
        log_change(log_file, error_message)
    return False

def create_exif_data(file_path, dt_eastern, log_file):
    try:
        exif_dict = {
            "0th": {
                piexif.ImageIFD.DateTime: dt_eastern.strftime('%Y:%m:%d %H:%M:%S')
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: dt_eastern.strftime('%Y:%m:%d %H:%M:%S'),
                piexif.ExifIFD.DateTimeDigitized: dt_eastern.strftime('%Y:%m:%d %H:%M:%S')
            }
        }
        exif_bytes = piexif.dump(exif_dict)
        image = Image.open(file_path)
        image.save(file_path, "jpeg", exif=exif_bytes)
        
        # Update file's access and modified times to match EXIF data
        timestamp = time.mktime(dt_eastern.timetuple())
        os.utime(file_path, (timestamp, timestamp))
        
        message = f"Created EXIF data for {file_path} with date {dt_eastern}"
        print(message)
        log_change(log_file, message)
        return True
    except Exception as e:
        error_message = f"Failed to create EXIF data for {file_path}: {e}"
        print(error_message)
        log_change(log_file, error_message)
    return False

def read_exif_data(file_path, log_file):
    exif_dict = log_exif_data(file_path, log_file)
    if exif_dict is None:
        return False
    try:
        log_message = f"Read EXIF data for {file_path}: {exif_dict}"
        log_change(log_file, log_message)
        return True
    except Exception as e:
        error_message = f"Failed to read EXIF data for {file_path}: {e}"
        print(error_message)
        log_change(log_file, error_message)
    return False

def update_file_dates(directory, log_file):
    eastern = pytz.timezone('US/Eastern')
    base_dir = os.path.abspath(directory)
    picture_count = 0
    video_count = 0
    altered_pictures = 0
    altered_videos = 0
    for root, dirs, files in os.walk(directory):
        dirs.sort()  # Sort subdirectories alphabetically/numerically
        files.sort()  # Sort files alphabetically/numerically
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png')):
                picture_count += 1
            elif file.endswith(('.mp4', '.mov')):
                video_count += 1
                continue  # Skip video files for now
            else:
                continue
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, base_dir)
            if relative_path == '.':
                continue
            try:
                # Extract date and time from filename
                date_str = file[:8]
                time_str = file[9:15]
                dt_str = date_str + time_str
                dt_utc = datetime.strptime(dt_str, '%Y%m%d%H%M%S')
                
                # Convert UTC to Eastern time
                dt_utc = pytz.utc.localize(dt_utc)
                dt_eastern = dt_utc.astimezone(eastern)
                
                # Convert to timestamp
                timestamp = time.mktime(dt_eastern.timetuple())
                
                # Update file's access and modified times
                os.utime(file_path, (timestamp, timestamp))
                
                # Read and log EXIF data before updating
                exif_data = log_exif_data(file_path, log_file)
                if exif_data is None:
                    if create_exif_data(file_path, dt_eastern, log_file):
                        message = f"Created and updated EXIF data for {relative_path} to {dt_eastern}"
                    else:
                        message = f"Failed to create EXIF data for {relative_path}"
                else:
                    # Check if EXIF data is already in sync with filename's date
                    exif_date = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
                    if exif_date:
                        exif_dt = datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S')
                        if exif_dt == dt_eastern:
                            message = f"EXIF data for {relative_path} is already in sync with {dt_eastern}"
                            print(message)
                            log_change(log_file, message)
                            continue

                    # Update EXIF data for pictures
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        if update_exif_data(file_path, dt_eastern, log_file):
                            message = f"Updated EXIF data for {relative_path} to {dt_eastern}"
                        else:
                            message = f"Failed to update EXIF data for {relative_path}"
                
                if file.endswith(('.jpg', '.jpeg', '.png')):
                    altered_pictures += 1
                elif file.endswith(('.mp4', '.mov')):
                    altered_videos += 1
            except Exception as e:
                message = f"Failed to update {relative_path}: {e}"
                print(message)
                log_change(log_file, message)
    summary_message = (f"Total pictures: {picture_count}, Total videos: {video_count}\n"
                       f"Altered pictures: {altered_pictures}, Altered videos: {altered_videos}\n"
                       f"Not altered pictures: {picture_count - altered_pictures}, Not altered videos: {video_count - altered_videos}")
    print(summary_message)
    log_change(log_file, summary_message)

def verify_file_dates(directory, log_file):
    eastern = pytz.timezone('US/Eastern')
    base_dir = os.path.abspath(directory)
    picture_count = 0
    video_count = 0
    altered_pictures = 0
    altered_videos = 0
    with open(log_file, 'w') as f:
        f.write("Verification Log\n")
    for root, dirs, files in os.walk(directory):
        dirs.sort()  # Sort subdirectories alphabetically/numerically
        files.sort()  # Sort files alphabetically/numerically
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png')):
                picture_count += 1
            elif file.endswith(('.mp4', '.mov')):
                video_count += 1
                continue  # Skip video files for now
            else:
                continue
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, base_dir)
            if relative_path == '.':
                continue
            try:
                # Extract date and time from filename
                date_str = file[:8]
                time_str = file[9:15]
                dt_str = date_str + time_str
                dt_utc = datetime.strptime(dt_str, '%Y%m%d%H%M%S')
                
                # Convert UTC to Eastern time
                dt_utc = pytz.utc.localize(dt_utc)
                dt_eastern = dt_utc.astimezone(eastern)
                
                # Get file's modified time
                file_timestamp = os.path.getmtime(file_path)
                file_dt = datetime.fromtimestamp(file_timestamp, eastern)
                
                # Compare the dates
                if dt_eastern != file_dt:
                    message = f"File {relative_path} is not in sync. Filename date: {dt_eastern}, File date: {file_dt}"
                    print(message)
                    log_change(log_file, message)
                    if file.endswith(('.jpg', '.jpeg', '.png')):
                        altered_pictures += 1
                    elif file.endswith(('.mp4', '.mov')):
                        altered_videos += 1
            except Exception as e:
                message = f"Failed to verify {relative_path}: {e}"
                print(message)
                log_change(log_file, message)
    summary_message = (f"Total pictures: {picture_count}, Total videos: {video_count}\n"
                       f"Altered pictures: {altered_pictures}, Altered videos: {altered_videos}\n"
                       f"Not altered pictures: {picture_count - altered_pictures}, Not altered videos: {video_count - altered_videos}")
    print(summary_message)
    log_change(log_file, summary_message)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update and verify file dates.")
    parser.add_argument('--directory', type=str, default=os.getcwd(), help='Directory to process')
    args = parser.parse_args()

    timestamp = int(time.time())
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'file_date_changes_{timestamp}.log')
    verify_log_file = os.path.join(log_dir, f'verify_file_date_changes_{timestamp}.log')
    
    update_file_dates(args.directory, log_file)
    # verify_file_dates(args.directory, verify_log_file)
