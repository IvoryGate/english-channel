# Encoding And Line Endings

This repository standardizes text files to avoid Windows encoding failures.

## Required Format

- Encoding: UTF-8 without BOM.
- Line endings: LF.
- Indentation: spaces.
- Final newline: required.
- Trailing whitespace: removed.

## Forbidden

- UTF-16 and UTF-16 LE/BE text files.
- Null bytes in source or documentation.
- CRLF in normal source, docs, JSON, YAML, Python, TypeScript, Markdown, and PowerShell files.
- Stray Unicode carriage characters such as U+0A0D.
- Windows PowerShell `Set-Content` default encoding when it writes UTF-16.

## PowerShell Rule

Windows PowerShell 5 may not support `-Encoding utf8NoBOM`. Use .NET explicitly:

```powershell
[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
```

Do not use bare `Set-Content` or `Out-File` for repository files.

## Agent Rule

Before and after large file generation, run:

```powershell
npm run check:encoding
```

If encoding violations appear, fix only the affected files and then continue. Do not run broad, slow whole-drive conversions.