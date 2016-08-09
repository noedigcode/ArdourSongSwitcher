#==============================================================================
# User edit section
#==============================================================================

# Number of tracks excluding Master
numtracks = 9

# Tracks to ignore when muting, e.g. [1,2] to ignore tracks 1 and 2
ignore = [1]

# List of songs. Each item in the list is in the form:
# ( songName, marker, listOfTracks )
# e.g. ('The House That Jack Built', 1, [4,5])
#      will start at marker 1 and unmute tracks 4 and 5.
songs = [
    ('Song 1', 0, [2,3] ),
    ('Song 2', 1, [4,5] ),
    ('Song 3', 2, [6,7] ),
    ('Song 4', 3, [8,9] )
]

# MIDI CC numbers to control songs and playback
cc_next = 34
cc_prev = 33
cc_play = 35
cc_playPause = 36
cc_stop = 37
cc_toCurrentSongStart = 38

# Mididings MIDI backend: 'alsa' or 'jack'
backend='alsa'

# Client to autoconnect the input MIDI port to
autoconnect='VMPK Output:0'

#==============================================================================
# End of user edit section
#==============================================================================

import liblo
import time
from mididings import *
from mididings import event
from mididings.extra.osc import OSCInterface

# -----------------------------------------------------------------------------
# Set up liblo
t = liblo.Address(3819)
s = liblo.send
# use s(t,'/my/osc/message',arg1,arg2...) to send

# -----------------------------------------------------------------------------
# Build tracks list from range, excluding ignore list
tracks = range(1,numtracks+1)
for i in ignore:
    tracks.remove(i)

# -----------------------------------------------------------------------------
# Mute specified track. 1=mute, 0=unmute
def ardour_muteTrack(track, mute):
    s(t,'/ardour/routes/mute',track,mute)

# -----------------------------------------------------------------------------
# Move Ardour playhead to specified marker, where zero is the start and nonzero
# markers must be after the start.
def ardour_gotoMarker(m):
    # Go to start, then next_marker until at the desired marker
    s(t,'/ardour/goto_start')
    time.sleep(0.1) # Seems Ardour doesn't always handle messages in quick succession as expected
    i=m
    while (i>0):
        s(t,'/ardour/next_marker')
        i -= 1
        time.sleep(0.1)

# -----------------------------------------------------------------------------
def ardour_switchSong(s):
    # Mute all tracks in tracks list
    for i in tracks:
        ardour_muteTrack(i,1)
    # For each song:
    song = songs[s]
    marker = song[1]
    trks = song[2]
    # Unmute all song tracks
    for i in trks:
        ardour_muteTrack(i,0)
    # Switch to song marker
    ardour_gotoMarker(marker)

# -----------------------------------------------------------------------------
def ardour_play():
    s(t,'/ardour/transport_play')

def ardour_stop():
    s(t,'/ardour/transport_stop')
    
def ardour_playPause():
    s(t,'/ardour/toggle_roll')

# -----------------------------------------------------------------------------
# Mididngs process function

currentSong = 0
ardour_switchSong(currentSong)

def mididingsProcess(n):
    global currentSong
    if (n.type == CTRL):
        if (n.data2 == 127):
            if n.data1 == cc_next:
                # Next song
                print('CC received: Next song')
                if currentSong < len(songs)-1:
                    currentSong += 1
                # Switch to next song in Ardour
                print('   Switching to song %d in Ardour'%currentSong)
                ardour_switchSong(currentSong)
                # Return program event to switch Mididings scene
                print('   Switching to scene %d'%(currentSong+1))
                return  event.ProgramEvent(1,1,currentSong+1)
            
            elif n.data1 == cc_prev:
                # Previoius song
                print('CC received: Previous song')
                if currentSong > 0:
                    currentSong -= 1
                # Switch to previous song in Ardour
                print('   Switching to song %d in Ardour'%currentSong)
                ardour_switchSong(currentSong)
                # Return program event to switch Mididings scene
                print('   Switching to scene %d'%(currentSong+1))
                return event.ProgramEvent(1,1,currentSong+1)
            
            elif n.data1 == cc_play:
                # Play
                print('CC received: Play')
                ardour_play()
            
            elif n.data1 == cc_playPause:
                # Play/Pause
                print('CC received: Play/Pause')
                ardour_playPause()
            
            elif n.data1 == cc_stop:
                # Stop
                print('CC received: Stop')
                ardour_stop()
                
            elif n.data1 == cc_toCurrentSongStart:
                # Goto current song start
                print('CC received: to current song start')
                ardour_switchSong(currentSong)
            # end if n.data1
        # end if n.data2
    #end if n.type
            
    elif (n.type == PROGRAM):
        if n.program-1 < len(songs):
            print('PRG received: %d'%n.program)
            currentSong = n.program-1
            # Switch to song in Ardour
            print('   Switching to song %d in Ardour'%currentSong)
            ardour_switchSong(currentSong)
            print('   Switching to scene %d'%(currentSong+1))
    
    return n

# -----------------------------------------------------------------------------
# Set up the rest of Mididings

hook(OSCInterface()) # For Livedings GUI

# Set up scenes
scenes = {}
# Song format: ('Song Name', 0, [2,3] )
i = 1
for song in songs:
    scenes[i] = Scene(song[0], Pass())
    i += 1

control = Process(mididingsProcess) >> Filter(PROGRAM) >> SceneSwitch()

config(backend=backend,
       in_ports=[('in',autoconnect)])

# -----------------------------------------------------------------------------
# Print some info for the user
print('\nArdour Song Switcher\n')
print('Use Livedings if you need a visual indicator')
print('(However, clicking on the Livedings interface will not switch songs)')
print('')
print('Number of tracks: %d'%numtracks)
temp = ''
for i in ignore:
    temp += '%d  '%i
print('Tracks to ignore: %s'%temp)
print('Songs:')
k = 1
for i in songs:
    temp = ''
    for j in i[2]:
        temp += '%d  '%j
    print('   %d) %s: Marker %d, Tracks %s'%(k,i[0],i[1],temp))
    k += 1
print('')
print('Use the following CC messages:')
print('   CC%d: Next song'%cc_next)
print('   CC%d: Prev song'%cc_prev)
print('   CC%d: Play'%cc_play)
print('   CC%d: PlayPause'%cc_playPause)
print('   CC%d: Stop'%cc_stop)
print('   CC%d: Go to start of currnent song'%cc_toCurrentSongStart)
print('You can also switch songs by sending Program messages')
print('\n')


# Run mididings
run( scenes=scenes, control=control )


