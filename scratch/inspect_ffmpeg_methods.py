import os
import zipfile
import glob
import subprocess

def inspect_methods():
    gradle_cache = os.path.expanduser("~/.gradle/caches/modules-2/files-2.1")
    pattern = os.path.join(gradle_cache, "io.github.junkfood02.youtubedl-android", "ffmpeg", "**", "*.aar")
    aars = glob.glob(pattern, recursive=True)
    if not aars:
        print("No AAR found")
        return
    
    aar = aars[0]
    with zipfile.ZipFile(aar, 'r') as zip_ref:
        zip_ref.extract('classes.jar', '.')
        with zipfile.ZipFile('classes.jar', 'r') as jar_ref:
            jar_ref.extract('com/yausername/ffmpeg/FFmpeg.class', '.')
            
    print("Extracted class. Running javap:")
    try:
        res = subprocess.run(["javap", "-p", "com/yausername/ffmpeg/FFmpeg.class"], capture_output=True, text=True)
        print("STDOUT:")
        print(res.stdout)
        print("STDERR:")
        print(res.stderr)
    except Exception as e:
        print("Failed to run javap:", e)
        
    # Clean up
    if os.path.exists('classes.jar'):
        os.remove('classes.jar')
    if os.path.exists('com/yausername/ffmpeg/FFmpeg.class'):
        os.remove('com/yausername/ffmpeg/FFmpeg.class')
        os.removedirs('com/yausername/ffmpeg')

if __name__ == "__main__":
    inspect_methods()
