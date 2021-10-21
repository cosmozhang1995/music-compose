# Usage: python main.py example.music

import wave
import math
import collections
import re
import sys, os

wav_filename = 'my.wav'
framerate = 11025
default_base_duration = 0.5

file = wave.open('my.wav', 'wb')

file.setnchannels(1)
file.setsampwidth(1)
file.setframerate(framerate)

center_c_frequence = 261.6
base_octa_scales = {
	'C': 0,
	'D': 1,
	'E': 2,
	'F': 2.5,
	'G': 3.5,
	'A': 4.5,
	'B': 5.5
}
for note in 'CDEFGAB':
	base_octa_scales['b' + note] = base_octa_scales[note] - 0.5
	base_octa_scales['#' + note] = base_octa_scales[note] + 0.5
def note_frequnce(note):
	octa = 0
	while len(note) > 1:
		if note[-1] == '+':
			octa += 1
			note = note[:-1]
		elif note[-1] == '-':
			octa -= 1
			note = note[:-1]
		else:
			break
	if note not in base_octa_scales:
		raise ValueError("illegal note: {}".format(note))
	return center_c_frequence * math.pow(2, octa + base_octa_scales[note] / 6)
nf = note_frequnce

class SoundSegment:
	def __init__(self, frequence=None, duration=None):
		self.frequence = frequence
		self.duration = duration
	def __str__(self):
		return "sound<{}Hz, {}s>".format(self.frequence, self.duration)

def parse_music(music_file):
	if isinstance(music_file, str):
		with open(music_file, 'r') as f:
			return parse_music(f)
	base_duration = default_base_duration
	sound = []
	started = False
	line_id = 0
	while True:
		line = music_file.readline()
		if line is None or len(line) == 0:
			break
		line_id += 1
		line = line.strip()
		if len(line) == 0:
			continue
		pos = line.find('--')
		if pos >= 0:
			comment = line[pos+2:].strip()
			line = line[:pos].strip()
		else:
			comment = None
		if not started:
			pos = line.find('=')
			if pos >= 0:
				arg_key = line[:pos].strip()
				arg_value = line[pos+1:].strip()
				if arg_key == 'speed':
					base_duration = default_base_duration / float(arg_value)
				continue
			else:
				started = True
		segments = []
		segment = ""
		for b in line:
			if b in (' ', '\t'):
				if len(segment) > 0:
					segments.append(segment)
					segment = ""
			else:
				segment += b
		if len(segment) > 0:
			segments.append(segment)
			segment = ""
		segment_id = 0
		for segment in segments:
			segment_id += 1
			sound.append(parse_music_segment(segment, base_duration=base_duration, line_id=line_id, segment_id=segment_id))
	return sound

def parse_music_segment(segment, base_duration=1, line_id=None, segment_id=None):
	duration = 1
	note = segment
	while len(note) > 1:
		if note[-1] == '~':
			duration += 1
			note = note[:-1]
		elif note[-1] == '\'':
			duration += 0.5
			note = note[:-1]
		elif note[-1] == '"':
			duration += 0.25
			note = note[:-1]
		else:
			break
	if duration == 1:
		duration = 0
		while len(note) > 1:
			if note[0] == '\'':
				duration += 0.5
				note = note[1:]
			elif note[0] == '"':
				duration += 0.25
				note = note[1:]
			else:
				break
		if duration == 0:
			duration = 1
	is_stop = False
	if note == '.':
		is_stop = True
	elif note == ',':
		is_stop = True
		duration *= 0.5
	elif note == ';':
		is_stop = True
		duration *= 0.25
	duration *= base_duration
	if is_stop:
		frequence = 0
	else:
		try:
			frequence = nf(note)
		except ValueError:
			raise ValueError("illegal segment {} at line:{} segment:{}. note is: {}".format(segment, line_id, segment_id, segment, note))
	return SoundSegment(frequence = frequence, duration = duration)

class BaseSound:
	def __init__(self, sound_file):
		self._sound = BaseSound.load_base_sound(sound_file)
	
	@staticmethod
	def load_base_sound(sound_file):
		if isinstance(sound_file, str):
			with open(sound_file, 'rb') as f:
				return BaseSound.load_base_sound(f)
		sound = []
		while True:
			data = sound_file.read(1)
			if len(data) == 0:
				break
			sound.append(int.from_bytes(data, byteorder='big', signed=False))
		return sound

	def make_sound(self, phase):
		"""extract a sound amplitude according to phase
		phase should be in range [0, 1]"""
		index = int(round(phase * (len(self._sound) - 1)))
		if index < 0 or index >= len(self._sound):
			print(phase, index, len(self._sound))
		return self._sound[index]


base_sound = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'base_sounds', 'default.bin')
sound = parse_music(sys.argv[1])
# print([str(x) for x in sound])
for segment in sound:
	frequence = float(segment.frequence)
	duration = float(segment.duration)
	num_bits = int(duration * framerate)
	ba = bytearray(num_bits)
	for i in range(num_bits):
		time = i / framerate * frequence
		phase = time - math.floor(time)
		# ba[i] = int(((math.sin(i / framerate * frequence * 2 * math.pi)) + 1) / 2 * 255)
		ba[i] = int(round(base_sound.make_sound(phase) * (math.sin(time * 2 * math.pi) + 1) / 2))
	file.writeframes(bytes(ba))

file.close()

os.system('afplay ' + wav_filename)
