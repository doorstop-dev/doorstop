import configparser
import importlib
import os
import sys
import operator

# inputs from the user for the traceability library to use to calculate the links
config = configparser.ConfigParser()
config.read('../../pyConfig.ini')
facade = importlib.import_module(config["Imports"]["Import1"])
traceLink = getattr(facade,config["FunctionName"]["Function"])
param1 = config["FunctionParams"]["Param1"]
param2 = config["FunctionParams"]["Param2"]

# function to calculate a new probability based on the feedback from the user
def new_probability(num1, num2):   #written as a function to be more easily updated to a different algorithm later
    return (num1+num2)/2
    
# calculates the traceabilty value for the given source and target with the given model(from a traceability library) and metric if needed
def traceabilityResult(source, target, targetFile, feedback, model, metric = None):
    with open(os.path.join(target, targetFile), 'r', encoding='latin1') as f: # open in readonly mode
        targetData = f.read()
        f.close()
    values = {}
    for sourceFilename in os.listdir(source):  # goes to each source file and compares the current target file
        with open(os.path.join(source,sourceFilename), 'r', encoding='latin1') as f:
            sourceData = f.read()
            f.close()
        if metric is None:
            result = traceLink(sourceData,targetData, model)
        else:
            result = traceLink(sourceData,targetData, model, metric)

        traceResult = round(result[1],2)
        tmpStr = targetFile+" "+sourceFilename
        if tmpStr in input:  # check if the user input their own traceability value for this file pair
            traceResult = new_probability(traceResult, float(feedback[tmpStr]))  # recalculating the probability

        values[sourceFilename] = traceResult  # stores the values with the source filename as the key of a dictionary
    return values

# outputs the traceability value for the given model to a file, organizes/labels the output
def outputValues(model, valuesDict, outputThreshold, curFile, output, repository):   
    sorted_valuesDict = {k: v for k, v in sorted(valuesDict.items(), key=operator.itemgetter(1), reverse=True)}
    for key in sorted_valuesDict:
        if (float(sorted_valuesDict[key]) >= outputThreshold):
            print("Source File: ",key, "Target File: ", curFile, "Traceability: ",sorted_valuesDict[key])
            output.write("<li>Model:"+ model + "\nSource File: <a href='https://github.com/{}/blob/main{}/{}'>".format(repository, sys.argv[1], key) + key + "</a>, Target File: <a href='https://github.com/{}/blob/main/{}'>".format(repository, curFile) + curFile + "</a>, Traceability: " + str(sorted_valuesDict[key]) + '</li>\n')

        

os.chdir('../../')
sourcePath = os.getcwd() + sys.argv[1]
targetPath = os.getcwd()
targetList = open(os.getcwd() + sys.argv[2], 'r', encoding='latin1').read().splitlines()
threshold = float(sys.argv[4]) # the threshold for what traceability values to return
feedbackSourceList = sys.argv[5].split(",")  # user feedback on the traceability value
feedbackTargetList = sys.argv[6].split(",")
feedbackNumList = sys.argv[7].split(",")
repositoryName = sys.argv[8]
print(feedbackSourceList, feedbackTargetList, feedbackNumList)

input={} # dictionary to be filled
for i in range (len(feedbackSourceList)):
    input[feedbackSourceList[i]+" "+feedbackTargetList[i]]=float(feedbackNumList[i]) # the dictionary with (targetFile, sourceFile) -- a tuple -- as the key and the probability as the value

for targetFilename in targetList: # calculate the traceability values for each target and source file pair

    valuesWMD = traceabilityResult(sourcePath, targetPath, targetFilename, input, param1, param2) #the model and metric passed in by the user

    # the other models for ds4se plugged in manually:
    # valuesSCM = traceabilityResult(sourcePath, targetPath, targetFilename, input, "word2vec", "SCM") 
    # valuesDoc = traceabilityResult(sourcePath, targetPath, targetFilename, input, "doc2vec")



    with open(os.getcwd() + sys.argv[3], 'a+', encoding='latin1') as writeFile:  # ouputting each of the values for the different models from DS4SE traceability library

        outputValues((param1 +", "+param2), valuesWMD, threshold, targetFilename, writeFile, repositoryName)
        # outputValues("word2vec, metric = SCM", valuesSCM, threshold, targetFilename, writeFile)
        # outputValues("doc2vec", valuesDoc, threshold, targetFilename, writeFile)

        writeFile.close()

