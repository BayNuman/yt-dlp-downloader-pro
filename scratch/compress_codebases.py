import re

def compress_codebase(file_path, output_path):
    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Clear translations (TRANSLATIONS dictionaries) to save token space
    # Remove dynamic python dictionaries
    print("Stripping TRANSLATIONS from python dictionary...")
    content = re.sub(r'TRANSLATIONS\s*=\s*\{.*?\}\s*(?=\n\w|\Z)', 'TRANSLATIONS = { /* Translation tokens stripped for token optimization */ }', content, flags=re.DOTALL)
    # Remove kotlin/android translations
    print("Stripping android translations...")
    content = re.sub(r'object\s+Translations\s*\{.*?\}\s*(?=\n\w|\Z)', 'object Translations { /* Android Translation tokens stripped */ }', content, flags=re.DOTALL)
    
    compressed_lines = []
    in_code_block = False
    
    for line in content.splitlines():
        if line.strip().startswith("```python") or line.strip().startswith("```kotlin"):
            in_code_block = True
            compressed_lines.append(line)
            continue
        elif line.strip().startswith("```") and in_code_block:
            in_code_block = False
            compressed_lines.append(line)
            continue
            
        if in_code_block:
            # Preserve imports, class signatures, function definitions, annotations, and comments
            stripped = line.strip()
            if stripped.startswith(("class ", "def ", "@", "#", '"""', "import ", "from ", "package ", "fun ", "interface ", "val ", "var ", "private ", "public ", "override ", "object ", "data class ")):
                compressed_lines.append(line)
            elif stripped == "":
                compressed_lines.append(line)
        else:
            compressed_lines.append(line)
            
    print(f"Writing compressed codebase to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(compressed_lines))

if __name__ == "__main__":
    import os
    os.makedirs("analysis_exports", exist_ok=True)
    compress_codebase("C:/Users/Salih/Desktop/yt_dlp_downloader_pro_desktop_codebase.md", "analysis_exports/compressed_desktop_codebase.md")
    compress_codebase("C:/Users/Salih/Desktop/yt_dlp_downloader_pro_android_codebase.md", "analysis_exports/compressed_android_codebase.md")
    print("Done!")
