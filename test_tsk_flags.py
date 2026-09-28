import pytsk3

imginfo = pytsk3.Img_Info("C:\\Users\\Ravi\\OneDrive\\Desktop\\mock_image.001")
fsinfo = pytsk3.FS_Info(imginfo, offset=0)

try:
    flags = fsinfo.block_stat(0).flags
    print(f"Block 0 flags: {flags}")
except Exception as e:
    print(f"Error block_stat: {e}")
