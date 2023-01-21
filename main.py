import sys

command = sys.argv.pop(1)
if command == 'writeTag':
    from cli import writeTag
elif command == 'readTags':
    from cli import readTags
elif command == 'changeDesktopReaderInfo':
    from cli import changeDesktopReaderInfo