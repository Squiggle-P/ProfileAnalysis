""" Boilerplate Info
AveragesAndReels.PY - Functions for binning and averaging multiple reels together
* 
* 

Created 08/27/17/PP - [R0]:



Edited  MM/DD/YY/NN - [R1]:

"""
from __future__ import print_function

import ProfileReader as PR
from math import isnan
import numpy


def Chunk2(ChunkMe, ChunkCount=3):
    """ This puts chunks it so the larger chunks are all first
    This is dumb.
    """
    TempArray = []
    k, m = divmod(len(ChunkMe), ChunkCount)
    for i in range(ChunkCount):
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
    for i in range(ChunkCount):
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


def AverageReel(RawReel, ChunkCount):
    AvgList = []
    ChunkedReel = ChunkList(RawReel, ChunkCount)
    for chunk in ChunkedReel:
        AvgList.append(numpy.mean(chunk))
    return AvgList


def AdjustProfile(InitialProfile, ChangeProfile, Gain):
    """
    This function applies <ChangeProfile>*Gain effects to <InitialProfile> and spits it back out
    :param InitialProfile: One list of cleaned profile data (no nan support)
    :param ChangeProfile: A list of the changes to an actuator array - length irrelevant
    :param Gain: Gain of the actuator on the profile data entered
    :return: List of new profile bin data w/ gain applied
    """

    NumOfChunks = len(ChangeProfile)
    NewProfile = []
    ChunkedProfile = ChunkList(InitialProfile, NumOfChunks)

    # Take a profile broken into actuator-associated chunks, apply changes based on movements in actuator
    # This is all assuming a flat response from the actuator. Let's not get any deeper, shall we?
    for chunk_index in range(len(ChunkedProfile)):
        for bin_index in range(len(ChunkedProfile[chunk_index])):
            ChunkedProfile[chunk_index][bin_index] = ChunkedProfile[chunk_index][bin_index] + ChangeProfile[
                                                                                                  chunk_index] * Gain

    # Unchunk the data and return
    for chunk in ChunkedProfile:
        for bin in chunk:
            NewProfile.append(bin)

    return NewProfile

if __name__ == "__main__":
    print("Hello World")

    import csv

    CWBinLimits = [15, 30]
    BWBinLimits = [15, 30]
    MoiBinLimits = [3, 17]
    ScanCountLimits = [70, 200]
    ReelAveragesDict = {}
    CPAverages = {}
    SBAverages = {}

    # Interface back to PR and pull data from CSV

    DatasetDictionary = PR.CSV2Arrays("TestData.csv",True)
    DatasetDictionary = PR.ScrubStandardDictionary(DatasetDictionary,LowMoiLimit = MoiBinLimits[0], HighMoiLimit = MoiBinLimits[1],
                            LowWtLimit = BWBinLimits[0], HighWtLimit=BWBinLimits[1],
                            LowScanLimit=ScanCountLimits[0], HighScanLimit=ScanCountLimits[1])

    DataOnlyDictionary = PR.JustTheData(DatasetDictionary)

    # Save all current roll and actuator averages in CSV for export use
    with open('RealRollAverages.csv', 'wb') as csvfile:
        writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
        for k, v in DataOnlyDictionary.iteritems():
            ReelAveragesDict[k] = RollAverages(v)
            writeobject.writerow([k])
            for reel in ReelAveragesDict[k]:
                writeobject.writerow(reel)

    with open('RealCPAverages.csv', 'wb') as csvfile:
        writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
        for k, v in DataOnlyDictionary.iteritems():
            CPAverages[k] = RollAverages(v, 122)
            writeobject.writerow([k])
            for actuatorbin in CPAverages[k]:
                writeobject.writerow(actuatorbin)

    with open('ReelSBAverages.csv', 'wb') as csvfile:
        writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
        for k, v in DataOnlyDictionary.iteritems():
            SBAverages[k] = RollAverages(v, 88)
            writeobject.writerow([k])
            for actuatorbin in SBAverages[k]:
                writeobject.writerow(actuatorbin)




        # Enable this to quickly report how many chunks of each length were spit out
        # counter = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # for i in othertempthing:
        #     counter[len(i)] = counter[len(i)] + 1
        # print counter
