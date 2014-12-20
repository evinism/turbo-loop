import pyaudio
import wave
import struct
import sys

CHUNK = 512 
FORMAT = pyaudio.paInt16 #paInt8
CHANNELS = 2 
RATE = 44100 #sample rate
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"
#Repeat coming after? Reduce Delay!

PREDELAY = 4500 #12000 summed for internal mic
POSTDELAY = 4500 #9000 for external (Jonny's)

LOOP_LENGTH_MAX = 1000000
LOOP_LENGTH = LOOP_LENGTH_MAX

p = pyaudio.PyAudio()

print("* recording")


frames = []
#2 separate channels
recordingl = [0]*(LOOP_LENGTH_MAX + 1)
recordingr = [0]*(LOOP_LENGTH_MAX + 1)
recIndex = 0;

MIN = -32767
MAX = 32767
#Compressor:
CUTOFF = 30000
RATIO = 0.7

isRecording = False

def callback(in_data, frame_count, time_info, status):
    data = in_data
    global recIndex
    global recording
    global isRecording
    #Handle Delays
    
    out = ""
    blockLoopLength = LOOP_LENGTH
    recBlockPos = (recIndex - PREDELAY + blockLoopLength)%blockLoopLength
    playBlockPos = (recIndex  + POSTDELAY)%blockLoopLength
    for i in range(frame_count):#For every sample in both in_data and recording
        sampleIn = struct.unpack("<hh", data[i*4:i*4+4])
        #Set the recording position and the play position, offset by latency
        recPos = (recBlockPos + i)%blockLoopLength
        playPos = (playBlockPos + i)%blockLoopLength
        sampleRec = (recordingl[recPos], recordingr[recPos])
        if not recPos%1000:#Quick output.
            print sampleRec[0]+sampleRec[1] #This actually works as a log scale, which is pretty cool
            
        #Perform recording and writing to buffers.
        if isRecording:
            recordingl[recPos] = sampleRec[0] + sampleIn[0]
            recordingr[recPos] = sampleRec[1] + sampleIn[1]
        #Update the output
        leftOut = recordingl[playPos]
        rightOut = recordingr[playPos]
        #Elbow compress the output
        if( leftOut > CUTOFF ):
            leftOut = RATIO*(leftOut-CUTOFF) + CUTOFF
        elif( leftOut < -CUTOFF):
            leftOut = RATIO*(leftOut+CUTOFF) - CUTOFF
        if( rightOut > CUTOFF ):
            rightOut = RATIO*(rightOut-CUTOFF) + CUTOFF
        elif( rightOut < -CUTOFF):
            leftOut = RATIO*(rightOut+CUTOFF) - CUTOFF
        #End COMPRESSION
        out = out + struct.pack("<hh", max(MIN, min(MAX,leftOut)), max(-MIN, min(MAX,rightOut)))
       
    action = pyaudio.paContinue
    
    recIndex = (recIndex + frame_count)%LOOP_LENGTH
    return (out, action)

playStream = p.open(format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            input=True,
            stream_callback=callback)
dat = raw_input("Begin Loop")
playStream.start_stream()
recIndex = 0
isRecording = True;
dat = raw_input("e to continue")
LOOP_LENGTH = recIndex
recIndex = 0
while( dat!="e" ):
    isRecording = not isRecording
    dat = raw_input("e to continue")

playStream.stop_stream()
playStream.close()

recStream.stop_stream()
recStream.close()
p.terminate()

#wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
#wf.setnchannels(CHANNELS)
#wf.setsampwidth(p.get_sample_size(FORMAT))
#wf.setframerate(RATE)
#wf.writeframes(b''.join(frames))
#wf.close()