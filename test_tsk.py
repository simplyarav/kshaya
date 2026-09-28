import pytsk3
import sys

try:
    imginfo = pytsk3.Img_Info("C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001")
    print(f"Image opened: {imginfo.get_size()} bytes")
    fsinfo = pytsk3.FS_Info(imginfo, offset=0)
    print(f"Filesystem found directly at offset 0!")
except Exception as e:
    print(f"Direct open failed: {e}")
    try:
        # Try finding partition
        vol = pytsk3.Volume_Info(imginfo)
        for part in vol:
            if part.flags == pytsk3.TSK_VS_PART_FLAG_ALLOC:
                print(f"Found allocated partition at offset {part.start * vol.info.block_size}")
                fsinfo = pytsk3.FS_Info(imginfo, offset=part.start * vol.info.block_size)
                print(f"Filesystem parsed: {fsinfo.info.ftype}")
    except Exception as e2:
        print(f"Volume open failed: {e2}")
