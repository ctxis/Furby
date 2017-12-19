# extract a18 audio files from a DLC file

dlcfile = 'tu012700.dlc'
with open(dlcfile, 'rb') as f:
    dlcdata = bytearray(f.read())

print(type(dlcdata))

audioheader = bytes([0,0,0x80, 0x3e])
pos = 0
n=0

while True:
    pos = dlcdata.find(audioheader, pos)-2
    if pos < 0:
        break
    audiolen = dlcdata[pos+1] << 8 | dlcdata[pos]
    print("found audio at 0x{:x} len 0x{:x}".format(pos, audiolen))
    chunk = bytes(dlcdata[pos:pos+audiolen+4])
    with open('chunks/{}.chunk{:04}.a18'.format(dlcfile, n), 'wb') as f:
        f.write(chunk)
    n += 1
    pos += 3

print(type(chunk))