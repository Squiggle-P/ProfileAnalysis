# Settings imported into ProfileSimulator.py
#
# Define good data - any reels with averages / counts outside of the below ranges will be considered bad and eliminated
CWBinLimits = [15, 30]
BWBinLimits = [15, 30]
MoiBinLimits = [3, 17]
ScanCountLimits = [70, 200]
#
# CD Sizing Data
CPActNum = 122
SBActNum = 88
RollsPerReel = 3
#
# Actuator gains - taken from MX controller
CPBWGain = -0.1328
CPCWGain = -0.0783
CPMoiGain = -0.1866
SBMoiGain = -0.0105
#
# If OutputCSVs == True, major profile datasets will be stored as CSVs. Recommend doing this for further analysis in
# Minitab or elsewhere.
OutputCSVs = True
#
# File names specified: These will be read/written regardless of OutputCSVs
RawDataFile = "TestData.csv"
#
# File names specified: These will be written if Output CSVs is true.
StoreRealCPAverages = "RealCPAverages.csv"
StoreRealRollAverages = "RealRollAverages.csv"
StoreRealSBAverages = "RealSBAverages.csv"
PostCPWeightDataFile = "NormalizedWeight.csv"
PostSBAdjustmentDataFile = "SteamboxEffect.csv"
PostCPMoistureNormalizationDataFile = "FinalRawData.csv"
StoreTemporaryCPAverages = "WeightWeightedCPAverages.csv"
StoreAdjustedCPAverages = "NewCPAverages.csv"
StoreAdjustedSBAverages = "NewSBAverages.csv"
StoreNewRollAverages = "NewRollAverages.csv"
