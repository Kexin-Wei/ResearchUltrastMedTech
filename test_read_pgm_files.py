from lib.pgm import PGMFile

# no cavitation intensity, thi off
pgmFile1 = PGMFile("data\test-pgm-files\7.pgm")
# head: pass
# rf:
#   1. size matched
#   2. rf[1764,39] = -61, pass
#   3. rf[2566,122] = -88, pass
# cavitation Intensity: pass

# no cavitation intensity, thi on
pgmFile2 = PGMFile("data\test-pgm-files\8.pgm")
# head: pass
# rf:
#   1. size: pass
#   2. rf[1764,39] = 16352, pass
#   3. rf[2566,122] = -17818, pass
# cavitation Intensity: pass

# has cavitation intensity, thi off
pgmFile3 = PGMFile("data\test-pgm-files\4-hifu.pgm")
# head: pass
# rf:
#   1. size
#   2. rf[1764,39] = -101, pass
#   3. rf[2566,122] = 11756, pass
# cavitation Intensity:  pass

print("done")
