import os
import math

nsamples = 50000
data = bytearray(nsamples)
for i in range(nsamples):
	t = float(i) / float(nsamples - 1)
	y = (math.sin(t * 2 * math.pi) + 1) / 2 * math.pow(t - 1, 2)
	y = math.pow(t - 1, 2)
	data[i] = int(round(y * 255))

base_sounds_dir = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'base_sounds')
if not os.path.exists(base_sounds_dir):
	os.mkdir(base_sounds_dir)
with open(os.path.join(base_sounds_dir, 'default.bin'), 'wb') as f:
	f.write(bytes(data))
