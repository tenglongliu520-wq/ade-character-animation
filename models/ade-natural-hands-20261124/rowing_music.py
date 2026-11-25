"""Create the original 96 BPM preview accompaniment."""
import math
from pathlib import Path
import wave

import numpy as np


RATE, BPM = 24000, 96
BEAT = 60 / BPM
ROOT = Path(__file__).resolve().parent


def main():
    audio = np.zeros(round(32 * BEAT * RATE), dtype=np.float64)
    rng = np.random.default_rng(2307)

    def mix(beat, samples):
        start = round(beat * BEAT * RATE)
        stop = min(start + len(samples), len(audio))
        audio[start:stop] += samples[:stop-start]

    def pluck(beat, midi, strength, tail):
        t = np.arange(round(tail * RATE)) / RATE
        angle = 2 * math.pi * 440 * 2 ** ((midi-69)/12) * t
        envelope = (1-np.exp(-t*410)) * np.exp(-t*4.9)
        tone = np.sin(angle) + .26*np.sin(2*angle)*np.exp(-t*6) + .10*np.sin(3*angle)*np.exp(-t*11)
        mix(beat, strength*envelope*tone)

    chords = [(55,59,62,67),(52,55,59,64),(48,55,60,64),(50,57,62,66)]
    for bar in range(8):
        root,third,fifth,top = chords[bar % len(chords)]
        start = bar*4
        if bar == 7:
            root,third,fifth,top = chords[0]
        for offset,note,gain in ((0,root-12,.105),(0,third,.052),(.5,fifth,.068),
                                 (1,top,.078),(1.5,third,.058),(2,root-12,.082),
                                 (2.5,fifth,.061),(3,third,.056),(3.5,top,.047)):
            if start+offset < 31:
                pluck(start+offset,note,gain,.64)
        for beat in range(start,start+4):
            if beat >= 30:
                break
            t = np.arange(round(.09*RATE)) / RATE
            drum = np.sin(2*math.pi*(92*t-165*t*t))*np.exp(-t*50)
            texture = rng.normal(0,1,len(t))*np.exp(-t*65)*.010
            mix(beat,(.055 if beat%2==0 else .029)*drum+texture)
    pluck(30,55,.070,1.1)
    pluck(30,62,.047,1.1)
    pluck(30.5,71,.051,.8)
    audio[-RATE//4:] *= np.linspace(1,0,RATE//4)
    with wave.open(str(ROOT/'rowing-beat.wav'),'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(np.asarray(np.clip(audio,-.94,.94)*32767,dtype='<i2').tobytes())


if __name__ == '__main__':
    main()
