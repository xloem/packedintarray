class PackedIntArray:
    '''
    A simple packed integer array.

    View and index a memory-like storage object as if it were composed of packed integers of an arbitrary bitwidth.

    Usage: PackedIntArray(bitwidth, storage, endian='little')[idx]

    If an integer is passed rather than a storage object, a new bytearray is allocated of sufficient size to hold that many bitwidths.
    '''
    def __init__(self, bitwidth, storage = None, length = None, bitoffset = 0, endian = 'little'):
        assert endian in ['little', 'big']
        assert storage is not None or length is not None
        if type(storage) is int:
            length = storage
            storage = None
        if storage is None:
            storage = bytearray((length * bitwidth - 1) // 8 + 1) # ceil(x / y) == (x - 1) // y + 1
        if length is None:
            length = len(storage) * 8 // self.bitwidth
        self.bitwidth = bitwidth
        self.storage = storage
        self.length = length
        self.bitoffset = bitoffset
        self.endian = endian
        self.get_range_shift = getattr(self, '_get_range_shift_' + endian)
        self.value_mask = (1 << bitwidth) - 1
    def __len__(self):
        return self.length
    def _get_range_shift_big(self, index, count=1):
        bitwidth = self.bitwidth
        bits = index * bitwidth + self.bitoffset
        offset1 = bits // 8
        offset2, bits2 = divmod(bits + bitwidth * count + 8, 8)
        return [offset1, offset2, 8 - bits2]
    def _get_range_shift_little(self, index, count=1):
        bitwidth = self.bitwidth
        bits = index * bitwidth + self.bitoffset
        offset1, bits1 = divmod(bits, 8)
        offset2 = (bits + bitwidth * count + 8) // 8
        return [offset1, offset2, bits1]
    def __getitem__(self, index):
        if type(index) is slice:
            assert index.step in [None,1] # todo if desired
            count = index.stop - index.start
            start, end, shift = self.get_range_shift(index.start, count)
            return type(self)(self.bitwidth, self.storage[start:end], count, shift, self.endian)
        else:
            start, end, shift = self.get_range_shift(index)
            return (int.from_bytes(self.storage[start:end], self.endian) >> shift) & self.value_mask
    def __setitem__(self, index, value):
        start, end, shift = self.get_range_shift(index)
        data = (int.from_bytes(self.storage[start:end], self.endian) & ~(self.value_mask << shift)) | (value << shift)
        self.storage[start:end] = data.to_bytes(end - start, self.endian)
    def __iter__(self):
        for idx in range(len(self)):
            yield self[idx]

def _test():
    import tqdm
    for bitwidth in [3, 9]:
        for endian in ['little', 'big']:
            ints = list(range(1<<bitwidth))
            testarray = PackedIntArray(bitwidth, storage=len(ints), endian='little')
            assert len(testarray) == len(ints)
            for idx in range(len(ints)):
                testarray[idx] = ints[idx]
            for idx in range(len(ints)):
                assert testarray[idx] == ints[idx]
            for start in tqdm.tqdm(range(len(ints)), desc=f'all {bitwidth}bit {endian} slices'):
                for stop in range(start, len(ints)):
                    subarray = testarray[start:stop]
                    subints = ints[start:stop]
                    for idx in range(len(subints)):
                        assert subarray[idx] == subints[idx]

if __name__ == '__main__':
    _test()
    print('Test passed.')
