'''
Created on Nov 20, 2018

@author: jjbun
'''
# http://blog.prosig.com/2006/02/17/standard-octave-bands/

"""
Preferred Series No R10 R20 R40 R80
1/N Octave 1/3 1/6 1/12 1/24
Steps/decade 10 20 40 80
"""

import math



#http://www.cross-spectrum.com/audio/articles/center_frequencies.html
# 1/24 octave
preferred = [
1.00,1.60,2.50,4.00,6.30,
1.03,1.65,2.58,4.12,6.50,
1.06,1.70,2.65,4.25,6.70,
1.09,1.75,2.72,4.37,6.90,
1.12,1.80,2.80,4.50,7.10,
1.15,1.85,2.90,4.62,7.30,
1.18,1.90,3.00,4.75,7.50,
1.22,1.95,3.07,4.87,7.75,
1.25,2.00,3.15,5.00,8.00,
1.28,2.06,3.25,5.15,8.25,
1.32,2.12,3.35,5.30,8.50,
1.36,2.18,3.45,5.45,8.75,
1.40,2.24,3.55,5.60,9.00,
1.45,2.30,3.65,5.80,9.25,
1.50,2.36,3.75,6.00,9.50,
1.55,2.43,3.87,6.15,9.75,
]

decades = [1., 10., 100., 1000., 10000.]

IOCTAVE = 3 # index into following array
OCTAVE = [24.0, 12.0, 6.0, 3.0, 1.0]
steps =         [1, 2, 4, 8, 24]


lowest_frequency = 2.5
highest_frequency = 22100.0

def main():
    
    prefs = []
    for j in range(5):
        for i in range(16):
            prefs.append(preferred[5*i+j])
    
    triplets = []
    frac = 3.0 / (OCTAVE[IOCTAVE] * 10.0)
    
    for decade in decades:
        for i in range(0, len(prefs), steps[IOCTAVE]):
            centre_freq = round(decade * prefs[i], 1)
            if centre_freq > highest_frequency:
                break
            if centre_freq < lowest_frequency:
                continue
            
            upper = centre_freq * math.pow(10.0, 0.5*frac)
            lower = centre_freq / math.pow(10.0, 0.5*frac)

            triplets.append( (lower, centre_freq, upper) )
    
    print 'static final double octave'+str(int(OCTAVE[IOCTAVE]))+'data[][] = new double[][] {'
          
    for t in triplets:
        print '     {%10.2f, %10.2f, %10.2f},' % (t[0], t[1], t[2])

    print '};'

    print 'NBINS', len(triplets)

if __name__ == '__main__':
    main()
