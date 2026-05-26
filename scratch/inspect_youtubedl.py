import os
import zipfile
import glob
import subprocess

def inspect_youtubedl():
    gradle_cache = os.path.expanduser("~/.gradle/caches/modules-2/files-2.1")
    pattern = os.path.join(gradle_cache, "io.github.junkfood02.youtubedl-android", "library", "**", "*.aar")
    aars = glob.glob(pattern, recursive=True)
    if not aars:
        print("No library AAR found")
        return
    
    aar = aars[0]
    with zipfile.ZipFile(aar, 'r') as zip_ref:
        zip_ref.extract('classes.jar', '.')
        with zipfile.ZipFile('classes.jar', 'r') as jar_ref:
            # Let's see what classes we have
            classes = [name for name in jar_ref.namelist() if 'YoutubeDL' in name and name.endswith('.class')]
            print("Found classes:", classes)
            for c in classes:
                jar_ref.extract(c, '.')
            
    print("Running javap on YoutubeDL.class:")
    try:
        res = subprocess.run(["javap", "-p", "com/yausername/youtubedl_android/YoutubeDL.class"], capture_output=True, text=True)
        print("YoutubeDL STDOUT:")
        print(res.stdout)
    except Exception as e:
        print("Failed to run javap:", e)

    # Clean up
    if os.path.exists('classes.jar'):
        os.remove('classes.jar')
    for root, dirs, files in os.walk('com', topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    if os.path.exists('com'):
        os.rmdir('com')

if __name__ == "__main__":
    inspect_youtubedl()
