import re

def strip_translations_only(file_path, output_path):
    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Python Desktop TRANSLATIONS dictionary
    print("Stripping TRANSLATIONS from python code...")
    content = re.sub(r'TRANSLATIONS\s*=\s*\{.*?\}\s*(?=\n\w|\Z)', 'TRANSLATIONS = { /* Translation tokens stripped for token optimization */ }', content, flags=re.DOTALL)
    
    # Kotlin/Android Translations object
    print("Stripping Translations object from kotlin code...")
    content = re.sub(r'object\s+Translations\s*\{.*?\}\s*(?=\n\w|\Z)', 'object Translations { /* Android Translation tokens stripped for token optimization */ }', content, flags=re.DOTALL)
    
    print(f"Writing translations-stripped codebase to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    import os
    os.makedirs("analysis_exports", exist_ok=True)
    strip_translations_only("C:/Users/Salih/Desktop/yt_dlp_downloader_pro_desktop_codebase.md", "analysis_exports/stripped_desktop_codebase_full.md")
    strip_translations_only("C:/Users/Salih/Desktop/yt_dlp_downloader_pro_android_codebase.md", "analysis_exports/stripped_android_codebase_full.md")
    print("Done!")
