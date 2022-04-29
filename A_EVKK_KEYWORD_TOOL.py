A_EVKK_KEYWORD_TOOL.py
Kellel on juurdepääs

J

M
Süsteemi atribuudid
Tüüp
Tekst
Suurus
31 kB
Kasutatud salvestusruum
31 kB
Asukoht
Herman_Petrov_võtmesõnad
Omanik
mina
Muudeti
Muutsin 18:53
Avatud
Avasin 18:56
Loodi
18:56 rakendusega Google Drive Web
Lisa kirjeldus
Vaatajad saavad alla laadida
import glob
import math
import os
import pandas as pd
from pathlib import Path
import re
from scipy.stats import chi2
import stanza
import tqdm
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)
stanza.download("et", processors="tokenize,pos,lemma")
nlp = stanza.Pipeline("et", processors="tokenize,pos,lemma")
info = "\nVALIKUKS SISESTAGE REA NUMBER"
splitter = "\n-------------------------------------------------------------"


def corpusProcessLoader(corpusFolder, corpusMenu):
    if len(os.listdir(corpusFolder)) != 1:
        for corpus in os.listdir(corpusFolder):
            referenceCorpusFile = os.path.join(corpusFolder, corpus)
            if os.path.isfile(referenceCorpusFile):
                corpusProcessor(referenceCorpusFile, corpusFolder, corpusMenu)
    else:
        print(
            "Viga! Valitud kaustas (",
            corpusFolder,
            ") ei ole lisatud faile. \nPalun lisage failid valitud kausta ning proovige uuesti.\n",
        )


def batchWriter(batchCount, lines, corpusFileName, corpusType):
    with open(
        corpusType
        + "processedData/data("
        + corpusFileName
        + ")"
        + str(batchCount)
        + ".csv",
        "w",
        encoding="utf-8",
    ) as corpusBatch:
        corpusBatch.writelines(lines)


def corpusSentenceFilter(sentence):
    sentenceFilters = [
        ("<.*?>", ""),
        ("http\S+|www\S+", " "),
        ("[^a-zA-ZõäöüšžÕÄÖÜŠŽ\\?\\!\\.\\,\\-\\:\\;]+", " "),
    ]
    for case, change in sentenceFilters:

        sentence = re.sub(case, change, sentence)
    return sentence


def corpusProcessor(corpusFile, corpusType, menuInputType):
    cleanResultsFolder()
    batchCount = 0
    corpusFile = os.path.basename(corpusFile)
    csvBatchSize = 1000
    print("Rakendus laeb faili: ", corpusFile, "\n")
    with open(corpusType + corpusFile, "r", encoding="utf-8") as corpus:
        lineCount = 0
        corpusLines = []
        for line in tqdm.tqdm(corpus.readlines()):
            line = corpusSentenceFilter(line)
            if len(line) < 2:
                continue
            lineCount += 1
            corpusLines.append(line + " \n\n")
            if lineCount % csvBatchSize == 0:
                batchWriter(
                    lineCount // csvBatchSize, corpusLines, corpusFile, corpusType
                )
                batchCount += 1
                corpusLines = []
        # write remainder
        if len(corpusLines) > 0:
            batchCount += 1
            batchWriter(
                (lineCount // csvBatchSize) + 1, corpusLines, corpusFile, corpusType
            )
    lemmaExtractor(corpusFile, batchCount, corpusType, menuInputType)
    print("\n", corpusFile, " korpus on loodud.\n")


def dictionaryOutput(corpusDictionary, outPutFile, typeOfWords, tokenCount, corpusName):
    if typeOfWords == "lemma" or typeOfWords == "vorm":
        data_items = corpusDictionary.items()
        data_list = list(data_items)
        if typeOfWords == "lemma":
            corpusData = pd.DataFrame(data_list, columns=["LEMMA", "SAGEDUS"])
        if typeOfWords == "vorm":
            corpusData = pd.DataFrame(data_list, columns=["SÕNAVORM", "SAGEDUS"])
        corpusData = corpusData.sort_values(by="SAGEDUS", ascending=False)
    if typeOfWords == "token":
        corpusData = pd.DataFrame({"KORPUS": [corpusName], "SAGEDUS": [tokenCount]})
    filepath = Path(outPutFile)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    corpusData.to_csv(filepath, index=False, encoding="utf-8-sig")


def lemmaExtractor(corpusName, batchCount, corpusType, menuInputType):
    corpusLoadertype = ""
    if corpusType == "referenceCorpus/":
        outputPath = [
            "referenceCorpusResults/lemmas",
            "referenceCorpusResults/nonLemmas",
            "referenceCorpusResults/totalTokens",
        ]
        corpusLoadertype = "reference"
    if menuInputType == "load":
        outputPath = [
            "focusCorpusResults/lemmas",
            "focusCorpusResults/nonLemmas",
            "focusCorpusResults/totalTokens",
        ]
        corpusLoadertype = "focus"
    nonLemmaDictionary = dict()
    lemmaDictionary = dict()
    counter = 1
    tokenCount = 0
    print("Korpus  (", corpusName, ") lemmatiseeritakse.")
    while batchCount >= counter:
        lemmaOutput = outputPath[0] + "/lemmas(" + corpusName + ").csv"
        nonLemmasOutput = outputPath[1] + "/nonLemmas(" + corpusName + ").csv"
        tokenOutput = outputPath[2] + "/totalTokens(" + corpusName + ").csv"

        with open(
            corpusType
            + "processedData/data("
            + corpusName
            + ")"
            + str(counter)
            + ".csv",
            "r",
            encoding="utf-8",
        ) as corpusPart:
            counter += 1
            inputText = corpusPart.read().rstrip()
            doc = nlp(inputText)
            for sent in tqdm.tqdm(doc.sentences):
                for word in sent.words:
                    tokenCount += 1
                    word.lemma = re.sub(
                        "-(?!\w)|(?<!\w)-|[^a-zA-ZõäöüšžÕÄÖÜŠŽ\\-]+",
                        "",
                        str(word.lemma),
                    )
                    if "-" not in word.text:
                        word.lemma = re.sub("-", "", word.lemma)
                    word.text = re.sub(
                        "-(?!\w)|(?<!\w)-|[^a-zA-ZõäöüšžÕÄÖÜŠŽ\\-]+", "", str(word.text)
                    )
                    if word.lemma in lemmaDictionary:

                        lemmaDictionary[word.lemma] += 1

                    else:
                        lemmaDictionary[word.lemma] = 1
                    if word.text in nonLemmaDictionary:

                        nonLemmaDictionary[word.text] += 1
                    else:
                        nonLemmaDictionary[word.text] = 1
    dictionaryOutput(lemmaDictionary, lemmaOutput, "lemma", "", corpusName)
    dictionaryOutput(nonLemmaDictionary, nonLemmasOutput, "vorm", "", corpusName)
    dictionaryOutput(nonLemmaDictionary, tokenOutput, "token", tokenCount, corpusName)
    countAllFolderWords(corpusLoadertype, corpusName)


def userTargetCorpusSubmission():
    corpusProcessLoader("focusCorpus/", "load")


def totalWordCount(corpusPath, outPutName, groupByColumn):
    corpusList = []
    for corpus in os.listdir(corpusPath):
        targetCorpusFile = os.path.join(corpusPath, corpus)
        if os.path.isfile(targetCorpusFile):
            corpusList.append(targetCorpusFile)
            allFromCorpus = pd.concat(
                (pd.read_csv(file) for file in corpusList), ignore_index=False
            )

            allFromCorpus = allFromCorpus.sort_values(by=["SAGEDUS"], ascending=False)

            allFromCorpus.groupby(groupByColumn, as_index=False).sum().sort_values(
                by=["SAGEDUS"], ascending=False
            ).to_csv(outPutName + ".csv", index=False, encoding="utf-8-sig")
    corpusList = []


def getCorpusSumWords(corpus):
    totalWords = corpus["SAGEDUS"].sum()
    return totalWords


def checkForFolders(corpusType, corpusName):
    output_path = ""
    created = False
    folderCount = 1
    while created != True:
        if corpusType == "focus":
            output_path = "fookus"
        else:
            output_path = "referents"
        generatedFolderName = (
            output_path + "korpus_" + corpusName + "_" + str(folderCount)
        )
        folderLemma = corpusType + "CorpusWords/" + generatedFolderName + "/lemmas/"
        folderNonLemma = (
            corpusType + "CorpusWords/" + generatedFolderName + "/nonLemmas/"
        )
        folderTotalTokens = (
            corpusType + "CorpusWords/" + generatedFolderName + "/totalTokens/"
        )
        folders = [folderLemma, folderNonLemma, folderTotalTokens]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
                created = True
        folderCount += 1
    return folders, generatedFolderName


def countAllFolderWords(typeOfCorpus, corpusName):
    folders, folder = checkForFolders(typeOfCorpus, corpusName)
    totalWordCount(
        typeOfCorpus + "CorpusResults/lemmas",
        folders[0] + "lemmas(" + folder + ")",
        "LEMMA",
    )
    totalWordCount(
        typeOfCorpus + "CorpusResults/nonLemmas",
        folders[1] + "nonLemmas(" + folder + ")",
        "SÕNAVORM",
    )
    totalWordCount(
        typeOfCorpus + "CorpusResults/totalTokens",
        folders[2] + "totalTokens(" + folder + ")",
        "KORPUS",
    )


def cleanResultsFolder():
    corpusResultsFolders = ["referenceCorpusResults/", "focusCorpusResults/"]
    resultFolders = ["lemmas/*", "nonLemmas/*", "totalTokens/*"]
    for corpus in corpusResultsFolders:
        for path in resultFolders:
            folder = glob.glob(corpus + path)
            for files in folder:
                os.remove(files)


def calculationProcessor(wordType):
    settings = loadSettings()
    referenceFolder = settings[0]
    focusFolder = settings[1]
    addOne = int(settings[2])
    focCorpusMinimumFreq = float(settings[3])
    wordAmount = settings[4]
    if settings[4] != "kõik":
        wordAmount = int(wordAmount)
    charSize = settings[5]
    stopWords = settings[6]
    if (referenceFolder != "") or (focusFolder != ""):
        columnType = ""
        if wordType == "lemma":
            columnType = "LEMMA"
            referenceCorpus = pd.read_csv(
                "referenceCorpusWords/"
                + referenceFolder
                + "/lemmas/lemmas("
                + referenceFolder
                + ").csv",
                encoding="utf-8",
            )
            focusCorpus = pd.read_csv(
                "focusCorpusWords/"
                + focusFolder
                + "/lemmas/lemmas("
                + focusFolder
                + ").csv",
                encoding="utf-8",
            )

        if wordType == "nonLemma":
            columnType = "SÕNAVORM"
            referenceCorpus = pd.read_csv(
                "referenceCorpusWords/"
                + referenceFolder
                + "/nonLemmas/nonLemmas("
                + referenceFolder
                + ").csv",
                encoding="utf-8",
            )
            focusCorpus = pd.read_csv(
                "focusCorpusWords/"
                + focusFolder
                + "/nonLemmas/nonLemmas("
                + focusFolder
                + ").csv",
                encoding="utf-8",
            )

        focusTokenCount = pd.read_csv(
            "focusCorpusWords/"
            + focusFolder
            + "/totalTokens/totalTokens("
            + focusFolder
            + ").csv",
            encoding="utf-8",
        )
        referenceTokenCount = pd.read_csv(
            "referenceCorpusWords/"
            + referenceFolder
            + "/totalTokens/totalTokens("
            + referenceFolder
            + ").csv",
            encoding="utf-8",
        )

        keynessFolder = (
            "võtmesõna_failid(" + str(focusFolder) + " ja " + str(referenceFolder) + ")"
        )

        focusCorpus = corpusToLowerCase(
            focusCorpus, columnType, charSize, wordType, stopWords
        )
        referenceCorpus = corpusToLowerCase(
            referenceCorpus, columnType, charSize, wordType, stopWords
        )

        focusTotalTokens = getCorpusSumWords(focusTokenCount)
        referenceTotalTokens = getCorpusSumWords(referenceTokenCount)

        unifiedCorpusLibrary = focusCorpus.merge(
            referenceCorpus, on=columnType, how="left"
        )
        unifiedCorpusLibrary = unifiedCorpusLibrary.fillna(0)

        unifiedCorpusLibrary = unifiedCorpusLibrary.sort_values(
            by=["SAGEDUS_x"], ascending=False
        )
        unifiedCorpusLibrary.to_csv(
            "combinedCorpus/combinedWordCount("
            + referenceFolder
            + "l"
            + focusFolder
            + ").csv",
            index=False,
            encoding="utf-8-sig",
        )
        keynessMath(
            unifiedCorpusLibrary,
            focusTotalTokens,
            referenceTotalTokens,
            wordType,
            addOne,
            focCorpusMinimumFreq,
            wordAmount,
            keynessFolder,
        )
    else:
        print("\nViga! Palun kontrollige üle valitud korpused.")


def loadSettings():
    with open("settings/settings.txt", "r", encoding="utf-8") as settings:
        settingsAttributes = settings.read()
        listAttributes = settingsAttributes.split("\n")
    return listAttributes
    


def updateSettings(settingsAttributes):
    with open("settings/settings.txt", "w", encoding="utf-8") as settings:
        for attribute in settingsAttributes:
            settings.write(attribute + "\n")
    settings.close()


def stopWordsRemoval(corpusType, comparedCorpus):
    columnName = ""
    if corpusType == "lemma":
        columnName = "LEMMA"
    else:
        columnName = "SÕNAVORM"
    stopWords = pd.read_csv(
        "estonianStopWords/estonian-stopwords-" + corpusType + ".csv",
        usecols=[columnName],
    )
    conditionCheck = comparedCorpus[columnName].isin(stopWords[columnName])
    comparedCorpus = comparedCorpus.drop(
        comparedCorpus[conditionCheck].index, inplace=True
    )

    return comparedCorpus


def keynessMath(
    corpus,
    focusAllFrequencies,
    referenceAllFrequencies,
    dataSetName,
    addOne,
    focCorpusMinimumFreq,
    wordAmount,
    outputFolder,
):
    corpusData = corpus
    wordType = corpusData.columns[0]
    chiKeynessResult = pd.DataFrame(
        columns=[
            wordType,
            "Võtmesus",
            "P-väärtus",
            "Fookus suhteline sagedus",
            "Referents suhteline sagedus",
        ]
    )
    logKeynessResult = pd.DataFrame(
        columns=[
            wordType,
            "Võtmesus",
            "P-väärtus",
            "Fookus suhteline sagedus",
            "Referents suhteline sagedus",
        ]
    )
    simpleMathResult = pd.DataFrame(
        columns=[
            wordType,
            "Võtmesus",
            "Fookus suhteline sagedus mil.",
            "Referents suhteline sagedus mil.",
        ]
    )
    logRatioResult = pd.DataFrame(
        columns=[
            wordType,
            "Võtmesus",
            "Fookus suhteline sagedus",
            "Referents suhteline sagedus",
        ]
    )

    focAll = focusAllFrequencies
    refAll = referenceAllFrequencies

    print(splitter)
    print("\nSõnede arv fookuskorpuses: ", focAll)
    print("Sõnede arv referentskorpuses: ", refAll)
    print(splitter)
    for ind in tqdm.tqdm(corpusData.index):

        word = corpusData[wordType][ind]

        a = focusCorpusWordFrequency = corpusData["SAGEDUS_x"][ind]
        if a >= focCorpusMinimumFreq:
            b = referenceCorpusWordFrequency = corpusData["SAGEDUS_y"][ind]

            c = allOtherFocusCorpusFrequencies = focAll - a
            d = allOtherReferenceCorpusFrequencies = refAll - b

            rF_f = relativeFrequencyFocusCorpusWord = a / (a + c)
            rF_r = relativeFrequencyReferenceCorpusWord = b / (b + d)

            e_1 = expectedRelativeFrequency_a = ((a + c) * (a + b)) / (a + c + b + d)
            e_2 = expectedRelativeFrequency_b = ((b + d) * (a + b)) / (a + c + b + d)
            e_3 = expectedRelativeFrequency_c = ((a + c) * (c + d)) / (a + c + b + d)
            e_4 = expectedRelativeFrequency_d = ((b + d) * (c + d)) / (a + c + b + d)

            fpmFc = frequencyPerMillionFocusCorpus = (a * 1000000) / (a + c)
            fpmRc = frequencyPerMillionReferenceCorpus = (b * 1000000) / (b + d)

            if b == 0:
                key_LL = logLikelihood = 2 * ((a * math.log(a / e_1)) + 0)
                key_LR = logRatio = float("inf")

            else:
                key_LL = logLikelihood = 2 * (
                    (a * math.log(a / e_1)) + (b * math.log(b / e_2))
                )
                key_LR = logRatio = math.log2(rF_f / rF_r)

            key_CHI = chiSquareTest = (
                ((a - e_1) ** 2) / e_1
                + ((b - e_2) ** 2) / e_2
                + ((c - e_3) ** 2) / e_3
                + ((d - e_4) ** 2) / e_4
            )

            key_SM = simpleMaths = (fpmFc + addOne) / (fpmRc + addOne)

            p_LL = probabilityValueOfLogLikelihood = chi2.sf(key_LL, 1)
            p_CHI = probabilityValueOfCHISquareTest = chi2.sf(key_CHI, 1)

            logKeynessResult = logKeynessResult.append(
                {
                    wordType: word,
                    "Võtmesus": key_LL,
                    "P-väärtus": p_LL,
                    "Fookus suhteline sagedus": rF_f,
                    "Referents suhteline sagedus": rF_r,
                },
                ignore_index=True,
            )

            chiKeynessResult = chiKeynessResult.append(
                {
                    wordType: word,
                    "Võtmesus": key_CHI,
                    "P-väärtus": p_CHI,
                    "Fookus suhteline sagedus": rF_f,
                    "Referents suhteline sagedus": rF_r,
                },
                ignore_index=True,
            )

            simpleMathResult = simpleMathResult.append(
                {
                    wordType: word,
                    "Võtmesus": key_SM,
                    "Fookus suhteline sagedus mil.": fpmFc,
                    "Referents suhteline sagedus mil.": fpmRc,
                },
                ignore_index=True,
            )

            logRatioResult = logRatioResult.append(
                {
                    wordType: word,
                    "Võtmesus": key_LR,
                    "Fookus suhteline sagedus": rF_f,
                    "Referents suhteline sagedus": rF_r,
                },
                ignore_index=True,
            )

    keynessValue(
        "Log-tõepära",
        logKeynessResult,
        dataSetName,
        wordAmount,
        outputFolder,
    )
    keynessValue(
        "Hii-ruut-test",
        chiKeynessResult,
        dataSetName,
        wordAmount,
        outputFolder,
    )
    keynessValue(
        "SimpleMath",
        simpleMathResult,
        dataSetName,
        wordAmount,
        outputFolder,
    )
    keynessValue(
        "Log-suhe",
        logRatioResult,
        dataSetName,
        wordAmount,
        outputFolder,
    )


def keynessValue(
    equationType, dataFrame, dataSetName, wordAmount, outputFolder
):
    dataFrame = dataFrame.sort_values(by=["Võtmesus"], ascending=False)
    if wordAmount != "kõik":
        dataFrame = dataFrame.head(wordAmount)
    keynessFolder = "keynessValues/" + outputFolder
    if os.path.exists(keynessFolder) == False:
        os.makedirs(keynessFolder)
    dataFrame.to_csv(
        "keynessValues/"
        + outputFolder
        + "/"
        + equationType
        + "("
        + dataSetName
        + ").csv",
        index=False,
        encoding="utf-8-sig",
    )


def mainInitiation():
    resetLog()
    menuInput = 0
    while menuInput != "4":
        print(
            "EVKK VÕTMESÕNADE LEIDJA 2022"
            + splitter
            + info
            + splitter
            + "\n1. Korpuste valik\n2. Võtmesõnade otsingu seaded\n3. Võtmesõnade otsing\n4. Välju "
        )
        menuInput = input()
        if menuInput == "1":
            menu_corpusSettings()
        if menuInput == "2":
            menu_keywordSettings()
        if menuInput == "3":
            menu_keywordSearch()
        if menuInput == "4":
            exit()
        resetLog()


def menu_corpusSettings():
    resetLog()
    settings = loadSettings()
    referenceCorpus = ""
    focusCorpus = ""
    menu_a_input = 0
    while menu_a_input != "4":
        print(
            "KORPUSE VALIK"
            + splitter
            + info
            + splitter
            + "\n1. Valitud referentskorpus = "
            + settings[0]
            + "\n2. Valitud fookuskorpus = "
            + settings[1]
            + "\n3. Loo uus korpus\n4. Tagasi"
        )
        menu_a_input = input()
        if menu_a_input == "1":
            referenceCorpus = a_1_corpusSettings(settings)
            updateSettings(referenceCorpus)
        if menu_a_input == "2":
            focusCorpus = a_2_corpusSettings(settings)
            updateSettings(focusCorpus)
        if menu_a_input == "3":
            a_3_corpusSettings(settings)
        resetLog()


def a_1_corpusSettings(settings):
    resetLog()
    refCorpusPath = "referenceCorpusWords/"
    listCorpusFiles = os.listdir(refCorpusPath)
    menu_a_1_input = 0
    fileIndex = 1
    while menu_a_1_input != "1":
        print("VALITUD REFERENTSKORPUS" + splitter + info + splitter + "\n1. Tagasi\n")
        for file in listCorpusFiles:
            fileIndex += 1
            print(str(fileIndex) + ". " + file)
        menu_a_1_input = input()
        if (menu_a_1_input != "") & (menu_a_1_input.isnumeric()):
            if (
                (menu_a_1_input != "1")
                & (int(menu_a_1_input) > 0)
                & (int(menu_a_1_input) <= (len(listCorpusFiles) + 1))
            ):
                selectedRefCorpus = listCorpusFiles[int(menu_a_1_input) - 2]
                print(
                    "Valitud referentskorpus on : "
                    + listCorpusFiles[int(menu_a_1_input) - 2]
                    + "\n"
                )
                menu_a_1_input = "1"
                settings[0] = selectedRefCorpus
                print(settings[0])
        fileIndex = 1
        resetLog()
    return settings


def a_2_corpusSettings(settings):
    resetLog()
    resetLog()
    focCorpusPath = "focusCorpusWords/"
    listCorpusFiles = os.listdir(focCorpusPath)
    menu_a_2_input = 0
    fileIndex = 1
    while menu_a_2_input != "1":
        print("VALITUD FOOKUSKORPUS" + splitter + info + splitter + "\n1. Tagasi\n")
        for file in listCorpusFiles:
            fileIndex += 1
            print(str(fileIndex) + ". " + file)
        menu_a_2_input = input()
        if (menu_a_2_input != "") & (menu_a_2_input.isnumeric()):
            if (
                (menu_a_2_input != "1")
                & (int(menu_a_2_input) > 0)
                & (int(menu_a_2_input) <= (len(listCorpusFiles) + 1))
            ):
                selectedFocCorpus = listCorpusFiles[int(menu_a_2_input) - 2]
                print(
                    "Valitud fookuskorpus on : "
                    + listCorpusFiles[int(menu_a_2_input) - 2]
                    + "\n"
                )
                menu_a_2_input = "1"
                settings[1] = selectedFocCorpus
        fileIndex = 1
        resetLog()
    return settings


def a_3_corpusSettings(settings):
    resetLog()
    menu_a_3_input = 0
    while menu_a_3_input != "3":
        print(
            "LOO UUS KORPUS"
            + splitter
            + info
            + splitter
            + "\n1. Loo uus referentskorpus (kaust: /referenceCorpus)\n2. Loo uus fookuskorpus  (kaust: /focusCorpus)\n3.Tagasi"
        )
        menu_a_3_input = input()
        if (menu_a_3_input == "1") or (menu_a_3_input == "2"):
            if menu_a_3_input == "1":
                resetLog()
                corpusProcessLoader("referenceCorpus/", "")
                input(" Jätkamiseks vajutage klahvi ENTER.\n")
                menu_a_3_input = "3"
            if menu_a_3_input == "2":
                resetLog()
                userTargetCorpusSubmission()
                menu_a_3_input = "3"
                input(" Jätkamiseks vajutage klahvi ENTER.\n")
        resetLog()


def menu_keywordSettings():
    resetLog()
    settings = loadSettings()
    menu_b_input = "0"
    while menu_b_input != "6":
        print(
            "VÕTMESÕNADE OTSINGU SEADED"
            + splitter
            + info
            + splitter
            + "\n1. Simple mathsi konstant n = "
            + settings[2]
            + "\n2. Sõna minimaalne esinemissagedus fookuskorpuses = "
            + settings[3]
            + "\n3. Maksimaalne näidatud sõnade hulk = "
            + settings[4]
            + "\n4. Väiketähestamine = "
            + settings[5]
            + "\n5. Stoppsõnade eemaldamine = "
            + settings[6]
            + "\n6. Tagasi"
        )
        menu_b_input = input()
        if menu_b_input == "1":
            addOne_N = b_1_keywordSettings(settings)
            updateSettings(addOne_N)
        if menu_b_input == "2":
            focCorpusMinimum = b_2_keywordSettings(settings)
            updateSettings(focCorpusMinimum)
        if menu_b_input == "3":
            maxWordRows = b_3_keywordSettings(settings)
            updateSettings(maxWordRows)
        if menu_b_input == "4":
            capitalLettering = b_4_keywordSettings(settings)
            updateSettings(capitalLettering)
        if menu_b_input == "5":
            stopWords = b_5_keywordSettings(settings)
            updateSettings(stopWords)
        resetLog()


def b_1_keywordSettings(settings):
    resetLog()
    menu_b_1_input = 0
    addOne_N = settings[2]
    addOneOptions = [1, 10, 100, 1000]
    while menu_b_1_input != "5":
        print(
            "SIMPLE MATH n KONSTANT"
            + splitter
            + info
            + splitter
            + "\n1. 1\n2. 10\n3. 100\n4. 1000\n5. Tagasi"
        )
        menu_b_1_input = input()
        if (menu_b_1_input != "") & (menu_b_1_input.isnumeric()):
            if (
                (menu_b_1_input != "5")
                & (int(menu_b_1_input) > 0)
                & (int(menu_b_1_input) <= 5)
            ):
                addOne_N = str(addOneOptions[int(menu_b_1_input) - 1])
                settings[2] = addOne_N
                print("\nMuudatus salvestatud\n")
                menu_b_1_input = "5"
        resetLog()
    return settings


def b_2_keywordSettings(settings):
    resetLog()
    menu_b_2_input = 0
    focCorpusMinimum = settings[3]
    focCorpusMinimumOptions = [1, 2, 3, 4, 5]
    while menu_b_2_input != "6":
        print(
            "FOOKUSKORPUSE SÕNA MINIMAALNE ESINEMISSAGEDUS"
            + splitter
            + info
            + splitter
            + "\n1. 1\n2. 2\n3. 3\n4. 4\n5. 5\n6. Tagasi"
        )
        menu_b_2_input = input()
        if (menu_b_2_input != "") & (menu_b_2_input.isnumeric()):
            if (
                (menu_b_2_input != "6")
                & (int(menu_b_2_input) > 0)
                & (int(menu_b_2_input) <= 6)
            ):
                focCorpusMinimum = str(focCorpusMinimumOptions[int(menu_b_2_input) - 1])
                settings[3] = focCorpusMinimum
                print("\nMuudatus salvestatud\n")
                menu_b_2_input = "6"
        resetLog()
    return settings


def b_3_keywordSettings(settings):
    resetLog()
    menu_b_3_input = 0
    maxWordRows = settings[4]
    maxWordsDisplayedOption = [50, 100, 200, "kõik"]
    while menu_b_3_input != "5":
        print(
            "MAKSIMAALNE NÄIDATUD SÕNADE HULK"
            + splitter
            + info
            + splitter
            + "\n1. 50\n2. 100\n3. 200\n4. Kõik\n5. Tagasi"
        )
        menu_b_3_input = input()
        if (menu_b_3_input != "") & (menu_b_3_input.isnumeric()):
            if (
                (menu_b_3_input != "5")
                & (int(menu_b_3_input) > 0)
                & (int(menu_b_3_input) <= 5)
            ):
                maxWordRows = str(maxWordsDisplayedOption[int(menu_b_3_input) - 1])
                settings[4] = maxWordRows
                print("\nMuudatus salvestatud\n")
                menu_b_3_input = "5"
        resetLog()
    return settings


def b_4_keywordSettings(settings):
    resetLog()
    menu_b_4_input = 0
    capitalLetter = settings[5]
    capitalLetterOption = ["sees", "väljas"]
    while menu_b_4_input != "3":
        print(
            "VÄIKETÄHESTAMINE"
            + splitter
            + info
            + splitter
            + "\n1. Sees\n2. Väljas\n3. Tagasi"
        )
        menu_b_4_input = input()
        if (menu_b_4_input != "") & (menu_b_4_input.isnumeric()):
            if (
                (menu_b_4_input != "3")
                & (int(menu_b_4_input) > 0)
                & (int(menu_b_4_input) <= 3)
            ):
                capitalLetter = str(capitalLetterOption[int(menu_b_4_input) - 1])
                settings[5] = capitalLetter
                print("\nMuudatus salvestatud\n")
                menu_b_4_input = "3"
        resetLog()
    return settings


def b_5_keywordSettings(settings):
    resetLog()
    menu_b_5_input = 0
    stopWords = settings[6]
    stopWordsOption = ["sees", "väljas"]
    while menu_b_5_input != "3":
        print(
            "STOPPSÕNADE EEMALDAMINE"
            + splitter
            + info
            + splitter
            + "\n1. Sees\n2. Väljas\n3. Tagasi"
        )
        menu_b_5_input = input()
        if (menu_b_5_input != "") & (menu_b_5_input.isnumeric()):
            if (
                (menu_b_5_input != "3")
                & (int(menu_b_5_input) > 0)
                & (int(menu_b_5_input) <= 3)
            ):
                stopWords = str(stopWordsOption[int(menu_b_5_input) - 1])
                settings[6] = stopWords
                print("\nMuudatus salvestatud\n")
                menu_b_5_input = "3"
        resetLog()
    return settings


def menu_keywordSearch():
    settings = loadSettings()
    menu_c_input = 0
    while menu_c_input != "2":
        print(
            "VÕTMESÕNADE OTSING"
            + splitter
            + "\nVALITUD FOOKUSKORPUS = "
            + settings[1]
            + "\nVALITUD REFERENTSKORPUS =  "
            + settings[0]
            + splitter
            + "\n1. Genereeri võtmesõnade failid\n2. Tagasi"
        )
        menu_c_input = input()
        if menu_c_input == "1":
            resetLog()
            print("Võtmesuse arvutamine on alanud, palun oodake.")
            print("Arvutatakse võtmesust lemmadega.")
            calculationProcessor("lemma")
            print("\n Arvutatakse võtmesust sõnavormidega.")
            calculationProcessor("nonLemma")
            print(
                "\nVõtmesõnad failid on loodud!\nVaadake kausta "
                '"keynessValue"'
                ".\n"
            )
            input(" Jätkamiseks vajutage klahvi ENTER.\n")
            menu_c_input = "2"
        resetLog()


def resetLog():
    os.system("cls" if os.name == "nt" else "clear")


def corpusToLowerCase(corpus, columnType, charSize, wordType, stopWords):
    corpus[columnType] = corpus[columnType].str.replace("_", "")
    if charSize == "sees":
        corpus[columnType] = corpus[columnType].str.lower()
    if stopWords == "sees":
        stopWordsRemoval(wordType, corpus)
    corpus = corpus[pd.to_numeric(corpus[columnType], errors="coerce").isna()]
    corpus = corpus.groupby([columnType], as_index=False)["SAGEDUS"].sum()
    return corpus


mainInitiation()
