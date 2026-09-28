import sys
import traceback
import time
try:
    with open(r'\\.\PhysicalDrive2', 'rb') as f:
        data = f.read(512)
        with open('uac_test_out.txt', 'w') as out:
            out.write('SUCCESS: Read 512 bytes')
except Exception as e:
    with open('uac_test_out.txt', 'w') as out:
        out.write('ERROR: ' + str(e) + '\n' + traceback.format_exc())
