""" Boilerplate Info
ProfileSimulator.PY - Using existing profile data (CSV) and existing MD/CD configuration data (config.txt), simulate
changes through the profile. This won't be perfect, but it should estimate large-scale changes (like addition of a
steambox) for rough estimates.

Created 09/01/17/PP - [R0]:


Edited  MM/DD/YY/NN - [R1]:

"""

from PSConfig import *
import ProfileReader as PR
import AveragesAndReels as AAR
import csv
import numpy

if __name__ == "__main__":

    CPGainDict = {"RL.BSWT (7)": CPBWGain,
                  "RL.MST (10)": CPMoiGain,
                  "RL.CNDWT (13)": CPCWGain,
                  "CTRL.HBDILFB (97)": 1}

    # Get Reels
    DatasetDictionary = PR.CSV2Arrays(RawDataFile, True)

    # Remove bad reels. Limits defined in PSConfig.py - user to edit if necessary - preconfigured limits very lax.
    DatasetDictionary = PR.ScrubStandardDictionary(DatasetDictionary,
                                                   LowMoiLimit=MoiBinLimits[0], HighMoiLimit=MoiBinLimits[1],
                                                   LowWtLimit=BWBinLimits[0], HighWtLimit=BWBinLimits[1],
                                                   LowScanLimit=ScanCountLimits[0], HighScanLimit=ScanCountLimits[1])

    # Remove extraneous MVDC data - just raw, good bin data: Array of float64s, length irrelevant
    DatasetDictionary = PR.JustTheData(DatasetDictionary)

    # Write Some Data
    if OutputCSVs:

        ReelAveragesDict = {}
        CPAverages = {}
        SBAverages = {}

        with open(StoreRealRollAverages, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            for k, v in DatasetDictionary.iteritems():
                ReelAveragesDict[k] = AAR.RollAverages(v, RollsPerReel)
                writeobject.writerow([k])
                for reel in ReelAveragesDict[k]:
                    writeobject.writerow(reel)

        with open(StoreRealCPAverages, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            for k, v in DatasetDictionary.iteritems():
                CPAverages[k] = AAR.RollAverages(v, CPActNum)
                writeobject.writerow([k])
                for actuatorbin in CPAverages[k]:
                    writeobject.writerow(actuatorbin)

        with open(StoreRealSBAverages, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            for k, v in DatasetDictionary.iteritems():
                SBAverages[k] = AAR.RollAverages(v, SBActNum)
                writeobject.writerow([k])
                for actuatorbin in SBAverages[k]:
                    writeobject.writerow(actuatorbin)

    # Normalize CWT using CDActuators
    CD_Act_Changes = []
    All_Act_Changes = []
    # Iterate through reels CWT profiles, making adjustments to actuators. We can ignore actuator limits here (right?)
    for reel in DatasetDictionary["RL.CNDWT (13)"]:
        ReelAvg = numpy.mean(reel)
        ChunkAverageReel = AAR.AverageReel(reel, CPActNum)
        ActChange = []
        for chunk in ChunkAverageReel:
            ActChange.append((ReelAvg - chunk) * (1 / CPCWGain))
            # print "Avg = %s" % ReelAvg
            # print "Profile = %s" % (chunk)
            # print "Move Actuator by: %s" % ActChange[len(ActChange)-1]
        All_Act_Changes.append(ActChange)

    TemporaryDatasetDictionary = {}
    AdjustedReels = []

    # Apply adjustments to all profiles
    for k, v in DatasetDictionary.iteritems():
        AdjustedReels = []
        for reel_i in xrange(len(v)):
            AdjustedReels.append(AAR.AdjustProfile(v[reel_i], All_Act_Changes[reel_i], CPGainDict[k]))
        TemporaryDatasetDictionary[k] = AdjustedReels

    if OutputCSVs:
        with open(PostCPWeightDataFile, 'wb') as csvfile:
            writeobject = csv.writer(csvfile, delimiter=',', quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            for k, v in TemporaryDatasetDictionary.iteritems():
                writeobject.writerow([k])
                for reel in v:
                    writeobject.writerow(reel)

    print "Hello World"
