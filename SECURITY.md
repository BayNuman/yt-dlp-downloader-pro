# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Active support  |

## Reporting a Vulnerability

If you discover a security vulnerability in **yt-dlp Downloader Pro**, please follow responsible disclosure:

1. **Do NOT** open a public GitHub issue for security vulnerabilities.
2. Send a detailed report to the maintainer via GitHub's private [Security Advisory](../../security/advisories/new) feature.
3. Include the following in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge your report within **48 hours** and aim to release a patch within **7 days** for critical issues.

## Security Considerations

- This application uses **yt-dlp** for downloading — always use the latest version to avoid known vulnerabilities.
- The desktop application bundles **ffmpeg** binaries — these are downloaded from official sources during build.
- The Android app requests only the **minimum required permissions** (storage read/write on Android < 10, notifications on Android 13+).
- No user data, URLs, or download history is transmitted to external servers.
