import pyaudio
import math
import wave
import struct
import time
import sys
import random

MAC_MAX_DB = 130
WAV_MAX_SOUND = 1 #1 is 70 dB SPL

SOUND_LEN = 2

trial=sys.argv[-1]
datafile = open('data'+str(trial)+'.txt', "w")

def synthComplex(freqs, timing=SOUND_LEN, fname="complex.wav"):
    frate = 44100.00
    datasize = int(timing * frate)
    amp=8000.0 
    sine_list=[]
    for x in range(datasize):
        samp = 0
        for f in freqs:
            samp = samp + f[1] * math.sin(2*math.pi*f[0]*(x/frate))
        sine_list.append(samp)
    wav_file=wave.open(fname,"w")
    nchannels = 1
    sampwidth = 2
    framerate = int(frate)
    nframes=datasize
    comptype= "NONE"
    compname= "not compressed"
    wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
    for s in sine_list:
        try:
            wav_file.writeframes(struct.pack('h', int(s*amp/2)))
        except struct.error as se:
            print s
            print str(se)
    wav_file.close()

def synthPure(freq, ampl=1, timing = SOUND_LEN, fname='pure.wav'):
    frate = 44100.00
    datasize = int(timing * frate)
    amp=8000.0 
    sine_list=[]
    for x in range(datasize):
        samp = ampl * math.sin(2*math.pi*freq*(x/frate))
        sine_list.append(samp)
    wav_file=wave.open(fname,"w")
    nchannels = 1
    sampwidth = 2
    framerate = int(frate)
    nframes=datasize
    comptype= "NONE"
    compname= "not compressed"
    wav_file.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
    for s in sine_list:
        wav_file.writeframes(struct.pack('h', int(s*amp/2)))
    wav_file.close()

def play_wav(wav_filename, chunk_size=1024):
    '''
    Play (on the attached system sound device) the WAV file
    named wav_filename.
    '''

    try:
        print 'Trying to play file ' + wav_filename
        wf = wave.open(wav_filename, 'rb')
    except IOError as ioe:
        sys.stderr.write('IOError on file ' + wav_filename + '\n' + \
        str(ioe) + '. Skipping.\n')
        return
    except EOFError as eofe:
        sys.stderr.write('EOFError on file ' + wav_filename + '\n' + \
        str(eofe) + '. Skipping.\n')
        return

    # Instantiate PyAudio.
    p = pyaudio.PyAudio()

    # Open stream.
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
        channels=wf.getnchannels(),
        rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(chunk_size)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(chunk_size)

    # Stop stream.
    stream.stop_stream()
    stream.close()

    # Close PyAudio.
    p.terminate()

# Decide on a fundamental freq and then do a Levitt Up-Down to determine what pitch I think it is.
# See if Terhardt et al's findings are accurate for a uniform function of pitch intensity as opposed to what he had found.

def rand_harmonics(freq, args):
    return random.random() * 2 * WAV_MAX_SOUND/args[0]

def virt_rand_harm(freq, args):
    return 0.0 if args[1] == 1 else random.random() * 2 * WAV_MAX_SOUND/(args[0] - 1)

def generate_complex_tone(minp=100, maxp=2000, fn=virt_rand_harm, df=datafile):
    f_1 = random.random() * (maxp - minp) + minp
    freqs = []
    csum = 0
    num_harms = 10
    df.write("Generating complex tone: \n")
    for i in range(1,num_harms):
        tup = (f_1 * i, fn(f_1 * i, [num_harms, i]))
        csum = csum + tup[1]
        df.write(str(tup[0]) + "\t" + str(tup[1]) + "\n")
        freqs.append(tup)

    tup = (f_1 * num_harms, WAV_MAX_SOUND - csum)
    df.write(str(tup[0]) + "\t" + str(tup[1]) + "\n")
    freqs.append(tup)

    df.write("\n\n")
    synthComplex(freqs, SOUND_LEN, "complex.wav")

def isYes(inp):
    return (inp == 'y') or (inp == 'Y') or (inp == "yes") or (inp == "Yes")

# Method of Limits, Staircase method (Levitt?)
tone_freq = 100
num_turnarounds = 10
step_size = 512
generate_complex_tone()

print "You will hear a pure tone followed by a complex tone. Report which sounds higher.\n"

synthPure(tone_freq)
play_wav("pure.wav")
play_wav("complex.wav")
user_in = raw_input("Was the pure tone higher than the complex tone? (y/n)")
isUp = not isYes(user_in)
step_size = step_size if isUp else -step_size

datafile.write("Turnaround\tFrequency\tStep Size\n")
for i in range(num_turnarounds):
    datafile.write(str(i)+"\t"+str(tone_freq)+"\t" + str(step_size) + "\n")
    while (step_size > 0 and isUp) or (step_size < 0 and not isUp):
        tone_freq = tone_freq + step_size
        synthPure(tone_freq)
        play_wav("pure.wav")
        play_wav("complex.wav")
        user_in = raw_input("Was the pure tone higher than the complex tone? (y/n)")
        isUp = not isYes(user_in)

    step_size = -step_size/2

datafile.write("Final frequency: "+str(tone_freq))

datafile.close()
# synthComplex([(440,.4),(880,0.3),(1200,0.1)], 2, "complex.wav")
# synthPure(500, .5, 2, "pure.wav")
# play_wav("complex.wav")
# play_wav("pure.wav")