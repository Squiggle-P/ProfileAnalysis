""" Boilerplate Info
AveragesAndReels.PY - Functions for binning and averaging multiple reels together
*
*

Created 08/27/17/PP - [R0]:



Edited  MM/DD/YY/NN - [R1]:

"""

import ProfileReader as PR
from math import isnan
import numpy


def Chunk2(ChunkMe, ChunkCount=3):
    """ This puts chunks it so the larger chunks are all first
    This is dumb.
    """
    TempArray = []
    k, m = divmod(len(ChunkMe), ChunkCount)
    for i in xrange(ChunkCount):
        TempArray.append(ChunkMe[i * k + min(i, m):(i + 1) * k + min(i + 1, m)])
    # return (ChunkMe[i*k+min(i,m),:(i+1) * k + min(i+1,m)] for i in range(ChunkCount))
    return TempArray

def ChunkList(ChunkMe,ChunkCount = 3):
    """
    This takes in a list of data and returns a list of the data separated into lists corresponding to chunks.
    :param ChunkMe: List to be chunked
    :param ChunkCount: Number of chunks out
    :return: List of chunks(lists)
    """
    TempArray = []
    k = float(len(ChunkMe)) / ChunkCount
    # k, m = divmod(len(ChunkMe),ChunkCount)
    for i in xrange(ChunkCount):
        TempArray.append(ChunkMe[int(round(i * k, 0)):int(round((i + 1) * k, 0))])
    # return (ChunkMe[i*k+min(i,m),:(i+1) * k + min(i+1,m)] for i in range(ChunkCount))
    return TempArray

def RollAverages(ArrayOfReels,NumOfRolls=3):
    """
    Remove NaNs, divide data into NumOfRolls groups, return averages
    :param ArrayOfReels: [[data1...data1120],[data1...data1120]...]
    :param NumOfRolls: integer, default 3
    :return: List of Lists roll averages
    """

    ArrayOfAverages = []
    ChunkedReels = []

    for reel in ArrayOfReels:
        NewReel = [x for x in reel if not isnan(x)]
        # print ChunkList(NewReel,NumOfRolls)

        ChunkedReels.append(ChunkList(NewReel,NumOfRolls))

    for reel in ChunkedReels:
        ReelAvgs = []
        for chunk in reel:
            ReelAvgs.append(numpy.mean(chunk))
        ArrayOfAverages.append(ReelAvgs)

    return ArrayOfAverages

if __name__ == "__main__":
    print "Hello World"

    CWBinLimits = [15, 30]
    BWBinLimits = [15, 30]
    MoiBinLimits = [3, 17]
    ScanCountLimits = [70, 200]
    ReelAveragesDict = {}

    # Interface back to PR and pull data from CSV

    DatasetDictionary = PR.CSV2Arrays("TestData.csv",True)
    DatasetDictionary = PR.ScrubStandardDictionary(DatasetDictionary,LowMoiLimit = MoiBinLimits[0], HighMoiLimit = MoiBinLimits[1],
                            LowWtLimit = BWBinLimits[0], HighWtLimit=BWBinLimits[1],
                            LowScanLimit=ScanCountLimits[0], HighScanLimit=ScanCountLimits[1])

    DataOnlyDictionary = PR.JustTheData(DatasetDictionary)

    for k,v in DataOnlyDictionary.iteritems():
        ReelAveragesDict[k] = RollAverages(v)
        print ReelAveragesDict[k]
    ActuatorAverages = {}

    for k, v in DataOnlyDictionary.iteritems():
        ActuatorAverages[k] = RollAverages(v, 122)

        # Enable this to quickly report how many chunks of each length were spit out
        # counter = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # for i in othertempthing:
        #     counter[len(i)] = counter[len(i)] + 1
        # print counter
