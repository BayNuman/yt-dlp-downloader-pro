import os
import zipfile
import glob

def find_aar_and_inspect():
    gradle_cache = os.path.expanduser("~/.gradle/caches/modules-2/files-2.1")
    pattern = os.path.join(gradle_cache, "io.github.junkfood02.youtubedl-android", "ffmpeg", "**", "*.aar")
    aars = glob.glob(pattern, recursive=True)
    if not aars:
        # try search yausername
        pattern2 = os.path.join(gradle_cache, "com.github.yausername.youtubedl-android", "ffmpeg", "**", "*.aar")
        aars = glob.glob(pattern2, recursive=True)
    
    if not aars:
        print("No ffmpeg AAR found in gradle cache. Let's list what we have in cache:")
        print("Checking path:", os.path.join(gradle_cache, "io.github.junkfood02.youtubedl-android"))
        return
    
    print("Found AARs:")
    for aar in aars:
        print("-", aar)
        with zipfile.ZipFile(aar, 'r') as zip_ref:
            # AARs contain a classes.jar inside them
            if 'classes.jar' in zip_ref.namelist():
                print("  Extracting classes.jar...")
                zip_ref.extract('classes.jar', '.')
                with zipfile.ZipFile('classes.jar', 'r') as jar_ref:
                    print("  Classes inside classes.jar:")
                    for name in jar_ref.namelist():
                        if 'FFmpeg' in name or 'ffmpeg' in name.lower():
                            print("    ", name)
                os.remove('classes.jar')

if __name__ == "__main__":
    find_aar_and_inspect()
