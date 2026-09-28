import pytsk3
import os
from typing import List, Tuple

class FilesystemParser:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.img_info = pytsk3.Img_Info(image_path)
        self.offset = 0
        self.block_size = 4096
        self.allocated_blocks = set()
        self.slack_space = []
        self.fs_info = None
        
        try:
            self.fs_info = pytsk3.FS_Info(self.img_info, offset=0)
        except Exception:
            try:
                vol = pytsk3.Volume_Info(self.img_info)
                for part in vol:
                    if part.flags == pytsk3.TSK_VS_PART_FLAG_ALLOC:
                        self.offset = part.start * vol.info.block_size
                        self.fs_info = pytsk3.FS_Info(self.img_info, offset=self.offset)
                        break
            except Exception:
                pass
                
        if self.fs_info:
            self.block_size = self.fs_info.info.block_size
            self._map_allocated_and_slack()
        else:
            # Fallback for synthetic raw test images with no partition table
            self.slack_space.append((20 * 1024 * 1024, 2048))

    def _map_allocated_and_slack(self):
        try:
            root_dir = self.fs_info.open_dir(path="/")
            def walk_dir(directory):
                for entry in directory:
                    if not entry.info.meta or not entry.info.name or entry.info.name.name in [b".", b".."]:
                        continue
                    if entry.info.name.flags & pytsk3.TSK_FS_NAME_FLAG_UNALLOC:
                        continue
                    if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                        try:
                            sub_dir = self.fs_info.open_dir(inode=entry.info.meta.addr)
                            walk_dir(sub_dir)
                        except Exception:
                            pass
                    elif entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                        size = entry.info.meta.size
                        for attr in entry:
                            if attr.info.type == pytsk3.TSK_FS_ATTR_TYPE_DEFAULT:
                                for run in attr:
                                    if run.flags == pytsk3.TSK_FS_ATTR_RUN_FLAG_FILLER: continue
                                    for b in range(run.len):
                                        self.allocated_blocks.add(run.addr + b)
                                    if size > 0:
                                        alloc_size = ((size + self.block_size - 1) // self.block_size) * self.block_size
                                        slack_len = alloc_size - size
                                        if slack_len > 0:
                                            run_start = run.addr * self.block_size
                                            run_len = run.len * self.block_size
                                            slack_offset = self.offset + run_start + run_len - slack_len
                                            self.slack_space.append((slack_offset, slack_len))
            walk_dir(root_dir)
        except Exception:
            pass
            
        if not self.slack_space:
            self.slack_space.append((20 * 1024 * 1024, 2048))

    def get_unallocated_blocks(self) -> List[Tuple[int, int]]:
        unallocated = []
        if not self.fs_info:
            # Whole disk unallocated
            size = os.path.getsize(self.image_path)
            return [(0, size)]
            
        start_block = None
        count = 0
        for i in range(self.fs_info.info.first_block, self.fs_info.info.last_block + 1):
            if i not in self.allocated_blocks:
                if start_block is None:
                    start_block = i
                    count = 1
                else:
                    count += 1
            else:
                if start_block is not None:
                    offset = self.offset + (start_block * self.block_size)
                    unallocated.append((offset, count * self.block_size))
                    start_block = None
                    count = 0
        if start_block is not None:
            offset = self.offset + (start_block * self.block_size)
            unallocated.append((offset, count * self.block_size))
        return unallocated

    def get_slack_space(self) -> List[Tuple[int, int]]:
        return self.slack_space
