# A simple Python script for converting opentype unicode-based
# Tamil characters to glyph format suitable for pasting in
# Affinity programs. You will have to reformat all the
# text in Affinity after pasting the clipboard and toggling
# to unicode. The app converts the Tamil unicode text to
# a string of glyph data that can be displayed inside
# Affinity apps. This works only for certain unicode-based open
# type fonts. The script reads the .ttf file, extracts the cmap and
# GSUB lookup tables and saves them in a temporary .xml file
# for use. If the opentype .ttf font file contains all the
# necessary glyphs for Tamil and if they all are also indexed in
# GSUB lookup tables, this Python program script will work!
#
# Usage: select and copy-paste true-type Tamil text in the upper window,
# press convert, press copy to copy converted format to clipboard
# press clear to clear both screens and the clipboard.
#
# Easiest way to copy the converted data is: open a new Text box
# in Affinity, press 'cmd v' to paste inside, 'cmd a' to select all,
# ctrl u to toggle to unicode, and then change font to the
# correct one.
#
# known problems: only level 1 substitution is ready and so
# it does not display some sanskrit characters like sri or ksha.
# Also char 'vi' in Latha font does not display correctly in Affinity.
#
# Note that copied text inside Affinity is not font
# characters, but glyph characters. So, you won't be able
# to change the font family. But you can resize the characters
# and any minor editing can be done using the glyph browser.
# Only Tamil and English characters are allowed. If you have
# other non-unicode font texts, you will have to convert and
# add them separately. Non-Tamil unicode text is passed through
# the program without conversion. All the formatting in the
# original text is also lost during clip and paste. So, you
# will have to reformat the text after pasting in Affinity.
# Some unicode-based opentype may not display correctly if
# they do not have all the glyph encoded in the GSUB list.
# Fonts like Vijaya, Akshar, TAU-encoded Tamil fonts, and many
# more work well.
#
# In Latha font, chars like 'vi' does not display correctly
# since it depends on GPOS data, and not GSUB. The glyph for this
# character 'vi is not inside .ttf file, and it has to be rendered
# using GPOS table by the Affinity app. It does so somewhat imperfectly,
# but otherwise it's fine.
#
# For other Indic languages, you will have to change some of the data
# inside the section below in this program. Tested up to 20-page
# MS Word Akshar or Vijaya font documents. Google Tamil fonts
# do not work, since they do not depend entirely on psts substitution
# rules in the GSUB table. They use more open-type features. Good luck!
#
# Chakravathy Mathiazhagan, IIT Madras.
#

# update 26 May 2022 -- added support for .ttc font collection files
# fixed a bug that happens when both taml and tml2 versions are present
# update 27 May 2022 -- added checking for GSUB table in font file

# added Hindi support. also added a middle window for showing unicode
# implemented multiple level lookups needed for Hindi
# This is a very messy implementation and there may be bugs when certain
# char combinations are encountered! But seems to work for Devanagari!
#
# Tried other languages like Malayalam, Telugu and Kannada
# Since they depend on vertical position GPOS engine, they don't
# work. Malayalam works somewhat except for vertical positioning.
#
# This is a messy program that works for Hindi partially, but mostly.
# It implements lookup table type 4 ligature substitutions and type 6
# lookahead and backtrack substitutions partially.
#

from tkinter import *
import sys
import clipboard
import tkinter.font as font
from fontTools.ttLib import TTFont
import xml.etree.ElementTree as ET

# check for available fonts
# if sys.version_info.major == 3:
#    import tkinter as tk, tkinter.font as tk_font
# else:
#    import Tkinter as tk, tkFont as tk_font

finalDisp = ""  # global final display return value
uniDisp = ""  # unicode value display for debugging

# enter the language ttf font below!
# strip and save a temp xml file with only GSUB and cmap tables for the font
# the conversion is faster, if the font .ttf or .ttc file contains
# fewer number of glyphs with just one language.

font2 = TTFont("akshar.ttf", fontNumber=0)
font2.saveXML("temp.xml", tables=["GSUB", "cmap"])

debug = False
defaultLang1 = False
defaultLang2 = False

# enable/disable various GSUB lookup table types for debugging
lookuptype4 = True
lookuptype5 = True
lookuptype6 = True
swapappends = True  # enable/disable prefix postfix swapping

# for deva only
doreph = True   # do reph/rakkar processing for Hindi, may not work correctly
dorakaar = True

# select only one language from below
# English is bypassed and so will also come
# do not select two or more, it won't work correctly!
# I do not know any of the Devanagari languages, but they
# seem to work mostly, but no guarantees!
#
# A few Hindi words like श्री, दर्द do not work! It is
# better to enter these manually inside Affinity.
# In some fonts, the reph sign appears as a rakaar at the
# bottom, and in other cases, the reph sign appears before.
# I really can't help here, since I do not know these rules.
# Fixed above problems by adding crude reph and rakaar engines.

# 19 Jun 2022
# added GSUB lookup type 5, but not sure if it is correct and latha.ttf still
# does not display Tamil vii வீ char correctly. Unicode sign ீ is placed wrongly.
# May be it depends on GPOS. But Tamil vi வி char works now, as it picks up the
# correct version of the postfix unicode sign ி!
# 19 Jun 2022
# added crude reph and rakaar sustitution engines. Somewhat works
# but not fully tested

Tamil = False  # enable only one!
Deva = True

# the following Dravidian languages don't work correctly
# as they rely mostly on GPOS engine to position char vertically!
# Malayalam seems to work a bit, except for vertical positioning
# I do not know these languages!
Malay = False
Telu = False
Kann = False

if Tamil:

    # ------------------------------------------------------
    # glyph IDs for pre-position/pre-base chars for Tamil, like in கெ கே கை கொ கோ கௌ
    # This list is for Tamil only!
    # These unicode char lists must be changed for other languages!
    # Please port it for other languages too!
    # Other languages like Hindi or Telugu depend heavily on GPOS rules
    # and may not work correctly in this GSUB based program!

    langID = "tml2"  # latest form of Tamil, skip the archaic form tml2
    langID2 = "taml"  # backup name if the first is not found
    prepChar = ["0xbc6", "0xbc7", "0xbc8"]  # single append preposition chars list கெ கே கை
    prep2Char = ["0xbca", "0xbcb", "0xbcc"]  # double append preposition chars list கொ கோ கௌ
    preapp2Char = ["0xbc6", "0xbc7", "0xbc6"]  # pre-append chars
    post2Char = ["0xbbe", "0xbbe", "0xbd7"]  # post-append chars
    postArch = ["0xbbe"]  # for skipping arch Tamil chars
    prepglyID = [0, 0, 0]  # pre-position glyph ID list initialization
    prep2glyID = [0, 0, 0]  # second pre-position glyph ID list initialization
    preapp2glyID = [0, 0, 0]  # pre-append glyph ID list initialization
    post2glyID = [0, 0, 0]  # post-append glyph ID list initialization
    uniRange = [0x0b80, 0x0bff]  # unicode range for the Tamil language
    # -----------------------------------------------------

if Deva:

    # ------------------------------------------------------
    # glyph IDs for pre-position/pre-base chars for Tamil, like in கெ கே கை கொ கோ கௌ
    # This list is for Deva only!
    # These unicode char lists must be changed for other languages!
    # Please port it for other languages too!
    # Other languages like Hindi or Telugu depend heavily on GPOS rules
    # and may not work correctly in this GSUB based program!

    langID = "dev2"  # latest form of Tamil, skip the archaic form tml2
    langID2 = "deva"  # backup name if the first is not found
    prepChar = ["0x94e", "0x93f"]  # single append preposition chars list கெ கே கை
    prep2Char = []  # double append preposition chars list கொ கோ கௌ
    preapp2Char = []  # pre-append chars
    post2Char = []  # post-append chars
    postArch = []  # for skipping arch Tamil chars
    prepglyID = [0, 0]  # pre-position glyph ID list initialization
    prep2glyID = []  # second pre-position glyph ID list initialization
    preapp2glyID = []  # pre-append glyph ID list initialization
    post2glyID = []  # post-append glyph ID list initialization
    uniRange = [0x0900, 0x097f]  # unicode range for the Hindi language
    rephsign = ["0x930"]  # special reph or ra sign for Hindi only
    viramasign = ["0x94d"] # virama or halant for Hindi
    # -----------------------------------------------------

if Malay:

    # ------------------------------------------------------
    # glyph IDs for pre-position/pre-base chars for Malayalam, like in கெ கே கை கொ கோ கௌ
    # This list is for Malay only!
    # These unicode char lists must be changed for other languages!
    # Please port it for other languages too!
    # Other languages like Hindi or Telugu depend heavily on GPOS rules
    # and may not work correctly in this GSUB based program!

    langID = "mlm2"  # latest form of Tamil, skip the archaic form tml2
    langID2 = "mlym"  # backup name if the first is not found
    prepChar = ["0xd46", "0xd47", "0xd48"]  # single append preposition chars list கெ கே கை
    prep2Char = ["0xd4a", "0xd4b", "0xd4c"]  # double append preposition chars list கொ கோ கௌ
    preapp2Char = ["0xd46", "0xd47", "0xd46"]  # pre-append chars
    post2Char = ["0xd3e", "0xd3e", "0xd57"]  # post-append chars
    prepglyID = [0, 0, 0]  # pre-position glyph ID list initialization
    prep2glyID = [0, 0, 0]  # second pre-position glyph ID list initialization
    preapp2glyID = [0, 0, 0]  # pre-append glyph ID list initialization
    post2glyID = [0, 0, 0]  # post-append glyph ID list initialization
    uniRange = [0x0d00, 0x0d7f]  # unicode range for the Malayalam language
    # -----------------------------------------------------

if Telu:

    # ------------------------------------------------------
    # glyph IDs for pre-position/pre-base chars for Telugu, like in கெ கே கை கொ கோ கௌ
    # This list is for Telugu only!
    # These unicode char lists must be changed for other languages!
    # Please port it for other languages too!
    # Other languages like Hindi or Telugu depend heavily on GPOS rules
    # and may not work correctly in this GSUB based program!

    langID = "tel2"  # latest form of Tamil, skip the archaic form tml2
    langID2 = "telu"  # backup name if the first is not found
    prepChar = []  # single append preposition chars list கெ கே கை
    prep2Char = []  # double append preposition chars list கொ கோ கௌ
    preapp2Char = []  # pre-append chars
    post2Char = []  # post-append chars
    prepglyID = []  # pre-position glyph ID list initialization
    prep2glyID = []  # second pre-position glyph ID list initialization
    preapp2glyID = []  # pre-append glyph ID list initialization
    post2glyID = []  # post-append glyph ID list initialization
    uniRange = [0x0c00, 0x0c7f]  # unicode range for the Malayalam language
    # -----------------------------------------------------

if Kann:

    # ------------------------------------------------------
    # glyph IDs for pre-position/pre-base chars for Kannada, like in கெ கே கை கொ கோ கௌ
    # This list is for Telugu only!
    # These unicode char lists must be changed for other languages!
    # Please port it for other languages too!
    # Other languages like Hindi or Telugu depend heavily on GPOS rules
    # and may not work correctly in this GSUB based program!

    langID = "knd2"  # latest form of Tamil, skip the archaic form tml2
    langID2 = "knda"  # backup name if the first is not found
    prepChar = []  # single append preposition chars list கெ கே கை
    prep2Char = []  # double append preposition chars list கொ கோ கௌ
    preapp2Char = []  # pre-append chars
    post2Char = []  # post-append chars
    prepglyID = []  # pre-position glyph ID list initialization
    prep2glyID = []  # second pre-position glyph ID list initialization
    preapp2glyID = []  # pre-append glyph ID list initialization
    post2glyID = []  # post-append glyph ID list initialization
    uniRange = [0x0c80, 0x0cff]  # unicode range for the Malayalam language
    # -----------------------------------------------------

print(font2.keys())

# check if GSUB is found
GSUBfound = False
for c in font2.keys():
    if c == 'GSUB':
        print ("GSUB found in the entered font file")
        GSUBfound = True

if not GSUBfound:
    print("GSUB not found in font file, quitting!")
    quit()

# parse xml tree. this xml is created in the same main directory
tree = ET.parse('temp.xml')

# getting the parent tag of
# the xml document
root = tree.getroot()

# read other link and subst data from the xml font file
substList = []  # final type 4 substitution data
subst1List = []  # final type 1 LA substitution data
subst1BTList = []  # final type 1 BT substitution data
subst6List = []  # final type 6 LA substitution data
subst6BTList = []  # final type 6 BT substitution data
subst5List = []  # final type 5 substitution data
subst5DefList = []  # type 5 classdef list
subst5RuleList = []  # type 5 rule list

# first get feature list
featlist = []  # list of features in GSUB
for c in root.iter('ScriptRecord'):
    scriptrecord = c.get("index")
    for d in c.iter('ScriptTag'):
        scripttag = d.get("value")
        for e in c.iter('FeatureIndex'):
            featindex = e.get("index")
            featvalue = e.get("value")
            featlist.append([scriptrecord, scripttag, featindex, featvalue])
#print(featlist)

lookuplist = []  # list of lookup indices
for c in root.iter('FeatureRecord'):
    featurerecordindex = c.get("index")
    for d in c.iter('FeatureTag'):
        featuretag = d.get("value")
        for e in c.iter('LookupListIndex'):
            lookuplistindex = e.get("index")
            lookuplistval = e.get("value")
            lookuplist.append([featurerecordindex, featuretag, lookuplistindex, lookuplistval])
#print("lookuplist = ", lookuplist)

# check which version of tml2 or taml is present
# search whole list first
for j in range(0, len(featlist)):
    if langID == featlist[j][1]:  # check first if tml2 is found
        defaultLang1 = True
    if langID2 == featlist[j][1]:  # check next if taml is found
        defaultLang2 = True

# print(defaultLang1, defaultLang2)

lkList = []  # linked list

if defaultLang1:
    # print("got the 1st language")
    for j in range(0, len(featlist)):
        if langID == featlist[j][1]:  # check first if tml2 is found
            lkList.append(featlist[j][3])
            print("default language found =", langID)

elif defaultLang2:
    # print("got to 2nd language")
    for j in range(0, len(featlist)):
        if langID2 == featlist[j][1]:  # check if the other archaic form taml is found
                lkList.append(featlist[j][3])
                print("language found is old version", langID2)

print("Feature table index: lkList =", lkList)

# now get link list of lookup tables to use in correct order
llList = []
if Deva:
    rephList = []
    rakaarList = []
    enablereph = False
    enablerakaar = False
for k in range(0, len(lkList)):
    for j in range(0, len(lookuplist)):
        if (lookuplist[j][0]) == lkList[k]:
            llList.append(lookuplist[j][3])
            if Deva:
                if "rphf" == lookuplist[j][1]:  # check rphf
                    rephList.append(lookuplist[j][3])
                    enablereph = True
                    print("reph feature found in table = " , lookuplist[j][3], " and enabled")
                if "rkrf" == lookuplist[j][1]:  # check rkrf
                    rakaarList.append(lookuplist[j][3])
                    enablerakaar = True
                    print("rakaar feature found in table = " , lookuplist[j][3], "a nd enabled")

print("Lookup table index: llList =", llList)
if Deva:
    print("reph table index: rephList =", rephList, "and reph enable = ", enablereph)
    print("rakaar table index: rakaarList =", rakaarList, "and rakaar enable =", enablerakaar)

# get reph substitution table here
if Deva and enablereph and doreph:
    j =0
    rephlookupList = []
    for k in range(0, len(rephList)):
        for c in root.iter('Lookup'):
            rephindex = c.get('index')
            if rephList[k] == rephindex:  # check in right order
                for d in c.iter('LigatureSet'):  # effectively search on for type 4 subst
                    forrephglyph = (d.get('glyph'))  # for this glyph, with glyph ID
                    for e in d.iter('Ligature'):
                        #rephcomp = str(e.get('components')).split(",")  # next component, split if there is more than 1
                        rephcomp = e.get('components')
                        # assume only one component now!
                        rephglyph = (e.get('glyph'))
                        rephlookupList.append([(forrephglyph),
                                          (rephcomp),(rephglyph)])

                        j = j + 1
                continue  # get substitute list in correct order

    print("number of reph substitutions to be made =", j)
    #print("rephlookupList = ", rephlookupList)

# get rakaar substitution table here
if Deva and enablerakaar and dorakaar:
    j =0
    rakaarlookupList = []
    for k in range(0, len(rakaarList)):
        for c in root.iter('Lookup'):
            rakaarindex = c.get('index')
            if rakaarList[k] == rakaarindex:  # check in right order
                for d in c.iter('LigatureSet'):  # effectively search on for type 4 subst
                    forrakaarglyph = (d.get('glyph'))  # for this glyph, with glyph ID
                    for e in d.iter('Ligature'):
                        rakaarcomp = str(e.get('components')).split(",")  # next component, split if there is more than 1
                        # rakaar has two components
                        rakaarglyph = (e.get('glyph'))
                        rakaarlookupList.append([(forrakaarglyph),
                                          (rakaarcomp),(rakaarglyph)])

                        j = j + 1
                continue  # get substitute list in correct order

    print("number of rakaar substitutions to be made =", j)
    #print("rakaarlookupList = ", rakaarlookupList)

# get char substitution type 4 list here
j = 0

for k in range(0, len(llList)):
    for c in root.iter('Lookup'):
        subsetindex = c.get('index')
        if llList[k] == subsetindex:  # check in right order
            for d in c.iter('LigatureSet'):  # effectively search on for type 4 subst
                forglyph = (d.get('glyph'))  # for this glyph, with glyph ID
                for e in d.iter('Ligature'):
                    substcomp = str(e.get('components')).split(",")  # next component, split if there is more than 1
                    # for k in range(0, len(substcomp)):
                    #     substcomp[k] = (substcomp[k])
                    substglyph = (e.get('glyph'))
                    substList.append([(forglyph),
                                      (substcomp),(substglyph)])
                    # if debug:
                    #     if (forglyph == 'uni0940'):  # for debugging a particular char
                    #         print("forglyph name= ", [(forglyph),
                    #                       (substcomp),(substglyph)])

                    j = j + 1
            continue  # get substitute list in correct order

print("number of substitutions type 4 to be made =", j)

if debug:
    print(substList)

# get char substitution type 5 lists here
j = 0
jj = 0
jjj = 0

for k in range(0, len(llList)):
    for c in root.iter('Lookup'):
        subset5index = c.get('index')
        if llList[k] == subset5index:  # check in right order
            for d in c.iter('LookupType'):  # effectively search for type 6 subst
                type5 = d.get('value')
                if not type5 == "5":
                    break  # break this d loop and go to next table
                print("found lookup table type 5 in the table number",subset5index, "and the type is" , type5)
                for e in c.iter('Glyph'):
                    glyphvalue = e.get('value')
                    subst5List.append([subset5index, glyphvalue])
                    j = j + 1

                for e in c.iter('ClassDef'):
                    glyphDefvalue = e.get('glyph')
                    glyphDefclass = e.get('class')
                    #print(glyphvalue, glyphclass)
                    subst5DefList.append([subset5index, glyphDefvalue, glyphDefclass])
                    jj = jj + 1

                for e in c.iter('SubClassSet'):
                    classindex = e.get('index')
                    isempty = e.get('empty')
                    if isempty == "1":
                        nextglyphclass = None
                        lookupruleindex = "0"
                        classrulenumber = "0"
                        jjj = jjj + 1
                        subst5RuleList.append([subset5index, classindex, classrulenumber, nextglyphclass, lookupruleindex])
                        continue
                    for f in e.iter('SubClassRule'):
                        classrulenumber = f.get('index')
                        for g in f.iter('Class'):
                            nextglyphclass = g.get('value')
                        for g in f.iter('LookupListIndex'):
                            lookupruleindex = g.get('value')
                            subst5RuleList.append([subset5index, classindex, classrulenumber, nextglyphclass, lookupruleindex])
                            jjj = jjj + 1

print("number of substitutions type 5 to be made =", j)
#print("susbt5List (table, glyph)=", subst5List)
print("number of type 5 classdef =", jj)
#print("subst5DefList (table, glyph, class) =", subst5DefList)
print("number of type 5 lookup rules =", jjj)
#print("subst5RuleList (table, class, rule number, next glyph class, lookup table) =", subst5RuleList)

# now get type 1 subst lookup list from type 5 rules
# create empty array
subst5lookup1List = []
for k in range(0, len(subst5RuleList)):
    subst5lookup1List.append([None, None, None, None, None, None])

j = 0
for k in range(0, len(subst5RuleList)):
    subst5lookup1List[k] = [subst5RuleList[k][0], subst5RuleList[k][4], None, None,
                            subst5RuleList[k][1], subst5RuleList[k][2]]
    for c in root.iter('Lookup'):
        subst5lookup1Listindex = c.get('index')
        #print("got here1")
        if subst5RuleList[k][4] == subst5lookup1Listindex:  # check in right order & assume it is type 1 table
            #print("got here2")
            for d in c.iter('Substitution'):  # effectively search for type 6 subst
                subst1in = d.get('in')
                subst1out = d.get('out')
                #print("glyphID substs", subst5RuleList[k][0], subst5lookup1Listindex, hex(font2.getGlyphID(subst1in)), hex(font2.getGlyphID(subst1out)))
                subst5lookup1List[k][2] = subst1in
                subst5lookup1List[k][3] = subst1out
                j = j + 1

print("number of type 5 referred type 1 substitutions =", j)
#print("subst5lookup1List (type 5 table, type 1 table, subst1in, susbt1out, class no., rule no.) =", subst5lookup1List)

# get char substitution type 6 LA list here, easier to work with glyph ID, so get glyph ID
j = 0

for k in range(0, len(llList)):
    for c in root.iter('Lookup'):
        subset6index = c.get('index')
        if llList[k] == subset6index:  # check in right order
            for d in c.iter('InputCoverage'):  # effectively search for type 6 subst
                index1 = d.get('index')
            for d in c.iter('SubstLookupRecord'):
                index2 = d.get('index')
            for d in c.iter('LookAheadCoverage'):
                index3 = d.get('index')

            temp1 = []
            for d in c.iter('InputCoverage'):  # effectively search on for type 4 subst
                for e in d.iter('Glyph'):  # effectively search on for type 4 subst
                    inputglyph = e.get('value')  # for in glyph
                    temp1.append(inputglyph)

            temp2 = ""
            for d in c.iter('SubstLookupRecord'):
                for e in d.iter('LookupListIndex'):
                    looklistindex = e.get('value')
                    temp2 = temp2+ looklistindex   # there only one value for the final look up table

            temp3 = []
            for d in c.iter('LookAheadCoverage'):
                for e in d.iter('Glyph'):
                    lookaheadglyph = e.get('value')
                    temp3.append(lookaheadglyph)

                subst6List.append([index1, index3, index2, temp1, temp3,temp2])
                #print([temp1, temp3, temp2])
                j = j + 1

           # if debug:
            #         if (inputglyph == 'uni093F'):  # for debugging a particular char
            #             print("inglyph name= ", [inputglyph, temp, looklistindex])

            continue  # get substitute list in correct order

print("number of LA substitutions type 6 to be made =", j)
#print((subst6List))

if debug:
    print(subst6List)

# get char substitution type 6 BT list here, easier to work with glyph ID, so get glyph ID
j = 0

for k in range(0, len(llList)):
    for c in root.iter('Lookup'):
        subset6BTindex = c.get('index')
        if llList[k] == subset6BTindex:  # check in right order
            for d in c.iter('InputCoverage'):  # effectively search on for type 4 subst
                indexBT1 = d.get('index')
            for d in c.iter('SubstLookupRecord'):
                indexBT2 = d.get('index')
            for d in c.iter('BacktrackCoverage'):
                indexBT3 = d.get('index')

            tempBT1 = []
            for d in c.iter('InputCoverage'):
                for e in d.iter('Glyph'):  # effectively search on for type 4 subst
                    inputglyph = (e.get('value'))  # for in glyph
                    tempBT1.append(inputglyph)

            tempBT2 = ""
            for d in c.iter('SubstLookupRecord'):
                for e in d.iter('LookupListIndex'):
                    looklistBTindex = e.get('value')
                    tempBT2 = tempBT2 + looklistBTindex

            tempBT3 = []
            for d in c.iter('BacktrackCoverage'):
                for e in d.iter('Glyph'):
                    backtrackglyph = (e.get('value'))
                    tempBT3.append(backtrackglyph)

                subst6BTList.append([indexBT1, indexBT3, indexBT2, tempBT1, tempBT3, tempBT2])
                j = j + 1

            # if debug:
            #         if (inputglyph == 'uni093F'):  # for debugging a particular char
            #             print("inglyph name= ", [inputglyph, temp, looklistindex])
            #     #

            continue  # get substitute list in correct order

print("number of BT substitutions type 6 to be made =", j)
#print((subst6BTList))

if debug:
    print(subst6BTList)

# get char substitution LA type 1 list here
j = 0

for k in range(0, len(subst6List)):
    for c in root.iter('Lookup'):
        subset6index = c.get('index')
        if subst6List[k][5] == subset6index:  # check in right order
            for d in c.iter('Substitution'):  # effectively search on for type 4 subst
                inglyph = (d.get('in'))  # for in glyph
                outglyph = (d.get('out'))  # for in glyph
                subst1List.append([subset6index, inglyph, outglyph])
                j = j + 1
                if debug:
                    if (inglyph == 'uni0940'):  # for debugging a particular char
                        print("inglyph name= ", [inglyph, outglyph])
            continue  # get substitute list in correct order

print("number of LA substitutions type 1 to be made =", j)
#print(subst1List)

if debug:
    print(subst1List)

# get char substitution BT type 1 list here, easier to work with glyph ID, so get glyph ID
j = 0

for k in range(0, len(subst6BTList)):
    for c in root.iter('Lookup'):
        subset6BTindex = c.get('index')
        if subst6BTList[k][5] == subset6BTindex:  # check in right order
            for d in c.iter('Substitution'):  # effectively search on for type 4 subst
                inglyph = (d.get('in'))  # for in glyph
                outglyph = (d.get('out'))  # for in glyph
                subst1BTList.append([subset6BTindex, inglyph, outglyph])
                j = j + 1
                if debug:
                    if (inglyph == 'uni0940'):  # for debugging a particular char in cmap names
                        print("inglyph name= ", [inglyph, outglyph])
            continue  # get substitute list in correct order

print("number of BT substitutions type 1 to be made =", j)
#print(subst1BTList)

if debug:
    print(subst1BTList)

k = 0
cmapList = []
# get mapped glyph names for unicode codes from cmap data
for Map in root.iter('map'):
    mapCode = str(Map.get('code'))
    glyphName = str(Map.get('name'))
    cmapList.append([mapCode, glyphName])
    k = k + 1
print("total number of all glyphs in cmap=", k)
#print(cmapList)

# find names for CR and LF names in cmap
CRName = ""
LFName = ""
SpaceName = ""
ZWNJName = ""
ZWJName = ""
rephname = ""
viramaname = ""

# list of vowel names
vowelname0a = ""
vowelname1b = ""
vowelname0 = ""
vowelname1 = ""
vowelname2 = ""
vowelname3 = ""
vowelname4 = ""
vowelname5 = ""
vowelname6 = ""
vowelname7 = ""
vowelname8 = ""
vowelname9 = ""
vowelname10 = ""
vowelname11 = ""
vowelname12 = ""
vowelname13 = ""
vowelname14 = ""
vowelname15 = ""

for k in range(0, len(cmapList)):
    if cmapList[k][0] == '0xa':
        CRName = cmapList[k][1]
    if cmapList[k][0] == '0xd':
        LFName = cmapList[k][1]
    if cmapList[k][0] == '0x20':
        SpaceName = cmapList[k][1]
    if cmapList[k][0] == '0x200c':
        ZWNJName = cmapList[k][1]
    if cmapList[k][0] == '0x200d':
        ZWJName = cmapList[k][1]
    if Deva and cmapList[k][0] == rephsign[0]:
        rephname = cmapList[k][1]
    if Deva and cmapList[k][0] == viramasign[0]:
        viramaname = cmapList[k][1]

    if Deva and cmapList[k][0] == '0x93e':
        vowelname0a = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x93f':
        vowelname1b = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x940':
        vowelname0 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x941':
        vowelname1 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x942':
        vowelname2 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x943':
        vowelname3 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x944':
        vowelname4 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x945':
        vowelname5 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x946':
        vowelname6 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x947':
        vowelname7 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x948':
        vowelname8 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x949':
        vowelname9 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x94a':
        vowelname10 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x94b':
        vowelname11 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x94c':
        vowelname12 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x94d':
        vowelname13 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x94e':
        vowelname14 = cmapList[k][1]
    if Deva and cmapList[k][0] == '0x94f':
        vowelname15 = cmapList[k][1]

#print("reph, virama name = ", rephname, viramaname)
#print("CR, LF names =", CRName, LFName)

# initialize some variables
l = 0
ll = 0

# get glyphIDs for pre-postion and post-position glyphs
# assume that they must be in the unicode fonts!
for l in range(0, len(prepChar)):
    for ll in range(0, len(cmapList)):
        if prepChar[l] == cmapList[ll][0]:
            prepglyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue

if debug:
    print("pre-position one char glyph IDs = ", prepglyID)  # like கெ கே கை

# assume that they must be in the unicode fonts!
for l in range(0, len(prep2Char)):
    for ll in range(0, len(cmapList)):
        if prep2Char[l] == cmapList[ll][0]:
            prep2glyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue

if debug:
    print("pre-position two char glyph IDs = ", prep2glyID)  # கொ கோ கௌ

# assume that they must be in the unicode fonts!
for l in range(0, len(preapp2Char)):
    for ll in range(0, len(cmapList)):
        if preapp2Char[l] == cmapList[ll][0]:
            preapp2glyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue

if debug:
    print("pre-append two char glyph IDs = ", preapp2glyID)  # like the first glyph in after கௌ

# assume that they must be in the unicode fonts!
for l in range(0, len(post2Char)):
    for ll in range(0, len(cmapList)):
        if post2Char[l] == cmapList[ll][0]:
            post2glyID[l] = font2.getGlyphID(cmapList[ll][1])
            continue

if debug:
    print("post-append char glyph IDs = ", post2glyID)  # like the third ள glyph after கௌ

# open Tk window
root = Tk()
root.title('A simple Unicode to opentype glyph format converter for Affinity programs')

# create Font in default display screen object
myFont = font.Font(family='Helvetica')

# copy some sample text into clipboard for testing the program

# clipboard.copy("தமிழ் மொழி கன் கண்ணன். Mathiazhagan. \n லக்‌ஷமி. லக்‌ஷ்மி? கீ சீ ஞீ டீ தீ நீ னீ றீ பீ ரீ லீ"
#                "மீ யீ ளீ  வீ வி \n "
#                "வீணாவி! ணி ணீ ஶ்ரீ ஸ்ரீ கை சித்து? தூ பு பூ மெ க்‌ஷ் மொ கை வெ றா சிந்து")

#clipboard.copy("अक्षय, राजा, रूपी, श्री , र्जी , दर्द  \n, mathi, test")

clipboard.copy("श्री, र्जी, दर्द, द्रआ, आर्द  र्दआ, क्क, द्क, द्म, रु, की,"
               " कि, क्ष, कि, रि, सि, खि, झि, टि, २६, एि, कूर  पूर  क्र  द्र  प्र,"
               " रूआ  र्रि  कैर  कोर्  र्की  कु  र्कु  र्कै   र्रि ")

clipText = clipboard.paste()  # text will have the content of clipboard
# sanskrit characters like ஶ்ரீ or க்‌ஷ need level 3 substitution not implemented here.

# print available fonts
# print(tk_font.families())
# print(tk_font.names())

print("")
print("*******************************************")
print("All GSUB lookup tables in the font file are now loaded and \n"
      "we are ready to convert the input!\n \nPlease select and enter/paste unicode data in the "
      "first screen, \npress Convert button, and press Copy botton to copy the converted glyph "
      "\nstring in the third screen to clipboard! "
      "The Clear button clears all screens \nand the clipboad."
      "\nThe second or middle screen shows"
      " the unicode numbers of the input string, \nused for debug purposes only.")
print("*******************************************")

def clear_all():
    global finalDisp
    global clipText
    finalDisp = ""
    clipboard.copy(finalDisp)  # now the clipboard content will be cleared
    clipText = clipboard.paste()  # text will have the content of clipboard
    textBox.delete("1.0", END)  # clear text boxes
    textBox2.delete("1.0", END)
    textBox3.delete("1.0", END)
    print('screen and clipboard cleared')


def copy_clipboard():  # copy glyph string in third window
    global finalDisp
    global clipText
    clipboard.copy(finalDisp)  # now the clipboard will have the data from third window
    clipText = clipboard.paste()  # text will have the content of clipboard
    print('copy to clipboard done')


# the main routine to read copied data in the first window, do all the substitutions,
# and display the final converted file in the third window! The second windows shows
# unicode values of the input chars, useful for debugging.

def retrieve_input():

    global finalDisp  # global so can be used in routines
    global uniDisp  # display unicode value in 2nd window for debugging

    finalDisp = ""  # initialize final display string in third window!
    uniDisp = ""  # initialize unicode display string 2nd window!

    #   manipulate the unicode string and convert
    inputValue = textBox.get("1.0", "end-1c")
    #inputValue = inputValue  # pad extra 3 space for level 3

    charAppend = ""  # char append variable in third window
    uniAppend = ""  # unicode char append variable in 2nd window for debug

    startpos = 0  # start postion of the char in the word

    # split input text into words for easier processing. Look for space breaks
    for ijk in range(startpos, len(inputValue)):  # for display unicode values in second window

        uniDisp = uniDisp + uniAppend  # for displaying unicode string 2nd window
        word = ""

        uniAppend = hex(ord(inputValue[ijk]))+","
        if ord(inputValue[ijk]) < 31:
            uniAppend = "\n"
            #charAppend = "\n"
            continue

        #read one word at a time by looking for space or CR

        for ii in range(startpos, len(inputValue)):
            word = word + (inputValue[ii])
            startpos = ii+1   # move to next postion
            if ord(inputValue[ii]) == 32:  # include space and below for word end!
                break  # break the above ii loop and continue

            # if ord(inputValue[ii]) < 32:  # include space and below for word end!
            #     word = word + "\r"
            #     continue  # break the above ii loop and continue

        # ignore empty spaces at the end of textbox
        if word == "":
            continue

        if debug:
            print("ijk, word =", ijk, word)

        wordname = [None]*(len(word)+2)  # pad 2 extra space for reph or rakaar search

        # convert chars in word to nameList (for special chars like CR, LF)
        for i in range(0, len(cmapList)):
            for i2 in range(0, len(word)):
                # assume all these are CR returns
                if ord(word[i2]) == 0x0a :
                    wordname[i2] = 'LFName'
                elif ord(word[i2]) == 0x0d :
                    wordname[i2] = 'CRName'
                elif ord(word[i2]) == 0x20:
                    wordname[i2] = 'SpaceName'
                elif ord(word[i2]) == 0x2008:
                    wordname[i2] = 'SpaceName'
                elif ord(word[i2]) == 0x2009:
                    wordname[i2] = 'SpaceName'
                elif ord(word[i2]) == 0x200c:
                    wordname[i2] = 'ZWNJName'
                elif ord(word[i2]) == 0x200d:
                    wordname[i2] = 'ZWJName'
                elif ord(word[i2]) == 0x2028 :  # line break actually
                    wordname[i2] = 'LineBreak'
                elif ord(word[i2]) == 0x2029 :  # para separator
                    wordname[i2] = 'ParaSeparator'
                elif hex(ord(word[i2])) == cmapList[i][0]:
                    wordname[i2] = cmapList[i][1]
                # elif (ord(word[i2]) < uniRange[0] or ord(word[i2]) > uniRange[1]):
                #     wordname[i2] = word[i2]

        if debug:
            print("ijk, wordname =", ijk, wordname)

        # swap first
        wordnamelen = len(wordname)  # word size has changed after reph
        for j2 in range(0, len(wordname)-1):  # skip the last one during swap!
            # now do swapping for pre-position chars
            if not swapappends:
                continue  # skip swapping prefix postfix glyphs
            for i4 in range(0, len(prepglyID)):
                if wordname[j2 + 1] == font2.getGlyphName(prepglyID[i4]):
                    tempvalue = wordname[j2]
                    wordname[j2] = wordname[j2 + 1]
                    wordname[j2 + 1] = tempvalue   # swapping done
                    continue

        for j2 in range(0, len(wordname) - 1):
            # now do swapping for pre-postion and post-position chars
            if not swapappends:
                continue  # skip swapping prefix postfix glyphs
            for i4 in range(0, len(prep2glyID)):
                if wordname[j2 + 1] == font2.getGlyphName(prep2glyID[i4]):
                    if j2 - 1 < 0:  # if in 0th place insert there, otherwise normal insert
                        wordname.insert(0, font2.getGlyphName(preapp2glyID[i4]))
                    else:
                        wordname.insert(j2, font2.getGlyphName(preapp2glyID[i4]))  # pre-position glyph normal insert
                    wordname[j2 + 2] = font2.getGlyphName(post2glyID[i4])  # post-position glyph insert after char
                    continue
        if debug:
            print("after all swapping done", wordname)

        # do rakaar now
        nextpos = 0
        rakaarreplace  = 0
        charpos = 0
        wordnamelen = len(wordname)

        for i2 in range(nextpos, wordnamelen):
            charpos = i2 - rakaarreplace  # current char position in word
            if Deva and enablerakaar and dorakaar:
                # search rakaar subst list
                # now do rakaar substitution
                for i3 in range(0, len(rakaarlookupList)):
                    if wordname[charpos] == rakaarlookupList[i3][0]:  # current char is in subst list
                        rakaarsubstword = wordname[charpos]
                        rakaarsubstComponent = rakaarlookupList[i3][1]
                        rakaarsubstValue = rakaarlookupList[i3][2]

                        if len(rakaarsubstComponent) == 2:  # do double chars subst
                            if (rakaarsubstComponent[0] == wordname[charpos + 1]) and (
                                    rakaarsubstComponent[1] == wordname[charpos + 2]):
                                #print("before rakaar =", wordname)
                                wordname[charpos] = rakaarsubstValue
                                del wordname[charpos + 1]  # delete that replaced char
                                del wordname[charpos + 1]
                                wordnamelen = wordnamelen - 2
                                nextpos = charpos + 1  # we deleted two char, so nextpos is +1
                                rakaarreplace = rakaarreplace + 2
                                rakaarsubstdone = True
                                #print("after rakaar =", wordname)
                                continue  # break i3 loop

        # do reph first
        rephreplace = 0
        wordnamelen = len(wordname)
        for jj2 in range(0, len(wordname)):
            j2 = jj2 - rephreplace
            if Deva and enablereph and doreph:
                # do reph swapping if first and second char are ra and virama
                # just shift by two chars and hope for the best!
                if wordname[j2] == rephname:
                    if len(wordname) > j2 + 2:
                        if wordname[j2 + 1] == viramaname:  # reph sequence found
                            #print("before reph =", wordname)
                            # ignore reph subst at the end of the word
                            if wordname[j2+2] == SpaceName or \
                                    wordname[j2+2] == "," or \
                                    wordname[j2 + 2] == None or \
                                    wordname[j2+2] == ".":
                                continue
                            # look for a vowel sign after the consonant
                            elif wordname[j2 + 3] == vowelname0 or \
                                wordname[j2 + 3] == vowelname9 or \
                                wordname[j2 + 3] == vowelname10 or \
                                wordname[j2 + 3] == vowelname11 or \
                                wordname[j2 + 3] == vowelname12 or \
                                wordname[j2 + 3] == vowelname15 or \
                                wordname[j2 + 2] == vowelname1b or \
                                wordname[j2 + 3] == vowelname0a:
                                # now shift reph sign to correct location
                                wordname[j2] = wordname[j2 + 2]
                                wordname[j2+1] = wordname[j2 + 3]
                                wordname[j2+2] = rephlookupList[0][2]
                                del wordname[j2 + 3]
                                #del wordname[j2 + 3]
                                rephreplace = rephreplace + 1
                            # look other type of vowel after consonant that attaches at bottom
                            elif wordname[j2 + 3] == vowelname1 or \
                                wordname[j2 + 3] == vowelname2 or \
                                wordname[j2 + 3] == vowelname3 or \
                                wordname[j2 + 3] == vowelname4 or \
                                wordname[j2 + 3] == vowelname5 or \
                                wordname[j2 + 3] == vowelname6 or \
                                wordname[j2 + 3] == vowelname7 or \
                                wordname[j2 + 3] == vowelname8 or \
                                wordname[j2 + 3] == vowelname13:

                                # move reph sign to correct location
                                del wordname[j2]
                                del wordname[j2]
                                wordname[j2 + 2] = rephlookupList[0][2]
                                rephreplace = rephreplace + 2

                            else:
                                # a simple consonant after reph
                                wordname[j2] = wordname[j2 + 2]
                                wordname[j2+1] = rephlookupList[0][2]
                                del wordname[j2+2]
                                rephreplace = rephreplace + 1
                            #print("after reph =", wordname)

        wordnamelen = len(wordname)
        # now the main loop for type 4 and type 6 substitutions
        for ij in range(0, len(wordname)):
            nextpos = 0
            replace = 0
            charpos = 0
            substdone = False  # subst not done yet

            for i2 in range(nextpos, wordnamelen):
                charpos = i2 - replace  # current char position in word

                # now do type 5 substitution
                for i3 in range(0, len(subst5List)):  # skip last subst char in word
                    if not lookuptype5:
                        continue  # skip type 5
                    if wordname[charpos] == subst5List[i3][1]:
                        rulenumber2 = "0"
                        classnumber2 = "0"
                        for i4 in range(0, len(subst5DefList)):
                            if wordname[charpos] == subst5DefList[i4][1] and subst5List[i3][0] == subst5DefList[i4][0]:

                                wordclass = subst5DefList[i4][2]
                                tablenumber = subst5DefList[i4][0]
                                # print("we are in classdef table stage 1 now",  tablenumber, wordclass,
                                #       wordname[charpos], wordname[charpos+1])

                                # now get the type 5 rule lookup rule
                                for i5 in range(0, len(subst5RuleList)):
                                    if tablenumber == subst5RuleList[i5][0] and wordclass == subst5RuleList[i5][1]:
                                        lookupnumber2 = subst5RuleList[i5][4]
                                        tablenumber2 = subst5RuleList[i5][0]
                                        classnumber2 = subst5RuleList[i5][1]
                                        rulenumber2 = subst5RuleList[i5][2]
                                        nextclassnumber2 = subst5RuleList[i5][3]

                                        if lookupnumber2 == "0":
                                            continue
                                        # print("we are in classdef table stage 2 now", tablenumber, wordclass,
                                        #       wordname[charpos], wordname[charpos + 1], lookupnumber2, tablenumber2,
                                        #       classnumber2, rulenumber2)
                                        for i6 in range(0, len(subst5lookup1List)):
                                            #print("stage 3 =", wordclass, classnumber2, nextclassnumber2, subst5RuleList[i5][4])
                                            if wordname[charpos+1] == subst5lookup1List[i6][2] and lookupnumber2 == \
                                                    subst5lookup1List[i6][1] \
                                                    and tablenumber2 == subst5lookup1List[i6][0] \
                                                    and rulenumber2 == subst5lookup1List[i6][5] \
                                                    and classnumber2 == subst5lookup1List[i6][4]:
                                                print("type 5 susbt before doing", ij, charpos, word, wordname,
                                                      tablenumber2, lookupnumber2,
                                                      wordname[charpos], wordname[charpos + 1])
                                                wordname[charpos+1] = subst5lookup1List[i6][3]
                                                replace = 0
                                                print("type 5 susbt after done", word, wordname, tablenumber,
                                                      lookupnumber2,
                                                      wordname[charpos], wordname[charpos + 1])
                                                continue

                        #break  # do only for first in subst5list table? not sure here!

                # the loop for type 4 subst with 3, 2 or 1 components

                # now do type 4 substitution
                for i3 in range(0, len(substList)):
                    if not lookuptype4:
                        continue  # skip type 4
                    if wordname[charpos] == substList[i3][0]:  # current char is in subst list
                        substword = wordname[charpos]
                        substComponent = substList[i3][1]
                        substValue = substList[i3][2]

                        if len(substComponent) == 3:  # first do triple chars subst
                            if wordname[charpos + 1] == ZWNJName:
                                if (substComponent[0] == wordname[charpos + 1]) and (
                                        substComponent[2] == wordname[charpos + 3]):
                                    # print("got to level 3 with zwj")
                                    wordname[charpos] = substValue
                                    del wordname[charpos + 1]  # delete that replaced char
                                    del wordname[charpos + 1]
                                    del wordname[charpos + 1]
                                    wordnamelen = wordnamelen - 3
                                    nextpos = charpos + 1  # we deleted one char, so nextpos is same
                                    replace = replace + 3
                                    substdone = True
                                    if debug:
                                        print("aft L3zwnj ij, charpos, nextpos, rep, len, new wordname", ij, charpos,
                                              nextpos,
                                              replace, wordnamelen, word[charpos],
                                              word[charpos + 1], word[charpos + 2], substword, substComponent,
                                              substValue)
                                    continue  # break i3 loop

                            else:  # if no ZWNJ, do these
                                if (substComponent[0] == wordname[charpos + 1]) and (substComponent[1]
                                                                                     == wordname[charpos + 2]) and (
                                        substComponent[2] == wordname[charpos + 3]):
                                    # print("got to level 3")
                                    wordname[charpos] = substValue
                                    del wordname[charpos + 1]  # delete that replaced char
                                    del wordname[charpos + 1]
                                    del wordname[charpos + 1]
                                    wordnamelen = wordnamelen - 3
                                    nextpos = charpos + 1  # we deleted these chars, so nextpos is +1
                                    replace = replace + 3
                                    substdone = True
                                    if debug:
                                        print("aft L3 ij, charpos, nextpos, rep, len, new wordname", ij, charpos,
                                              nextpos, replace, wordnamelen, word[charpos],
                                              word[charpos + 1], word[charpos + 2], substword, substComponent,
                                              substValue)
                                    continue  # break i3 loop

                        elif len(substComponent) == 2:  # do double chars subst
                            if (substComponent[0] == wordname[charpos + 1]) and (
                                    substComponent[1] == wordname[charpos + 2]):
                                # print("got to level 2")
                                wordname[charpos] = substValue
                                del wordname[charpos + 1]  # delete that replaced char
                                del wordname[charpos + 1]
                                wordnamelen = wordnamelen - 2
                                nextpos = charpos + 1  # we deleted two char, so nextpos is +1
                                replace = replace + 2
                                substdone = True
                                if debug:
                                    print("aft L2 ij, charpos, nextpos, rep, len, new wordname", ij, charpos, nextpos,
                                          replace, wordnamelen, word[charpos],
                                          word[charpos + 1], word[charpos + 2], substword, substComponent, substValue)
                                continue  # break i3 loop

                        elif len(substComponent) == 1:  # do single char subst
                            if substComponent[0] == wordname[charpos + 1]:
                                # print("got to level 1")
                                wordname[charpos] = substValue
                                del wordname[charpos + 1]  # delete that replaced char
                                wordnamelen = wordnamelen - 1
                                nextpos = charpos + 1  # we deleted one char, so nextpos is +1
                                replace = replace + 1
                                substdone = True
                                if debug:
                                    print("aft L1 ij, charpos, nextpos, rep, len, new wordname", ij, charpos, nextpos,
                                          replace, wordnamelen, word[charpos],
                                          word[charpos + 1], substword, substComponent, substValue)
                                continue  # break i3 loop

                # type 6 LA substitution
                # now do type 6 substitution
                for i3 in range(0, len(subst6List)):
                    if not lookuptype6:
                        continue  # skip type 6
                    # print("subst6 ", wordname[charpos], subst6List[i3][0][0])
                    for i4 in range(0, len(subst6List[i3][3])):
                        if wordname[charpos] == subst6List[i3][3][i4]:  # current char is in type 6 subst list
                            # print("before subst6 ", len(subst6List[i3][4]), wordname[charpos], subst6List[i3][3][0])
                            if subst6List[i3][0] == '0' and subst6List[i3][1] == '0': # only one char
                                #print("before subst6 ", len(subst6List[i3][4]), wordname[charpos], subst6List[i3][3][0])
                                for j3 in range(0, len(subst6List[i3][4])):
                                    if wordname[charpos + 1] == subst6List[i3][4][j3]:  # see if next word char is in list
                                        if debug:
                                            print("after subst6 0 0 ", (subst6List[i3][4][j3]), wordname[charpos + 1],
                                                  subst6List[i3][5])
                                        for k3 in range(0, len(subst1List)):
                                            if subst6List[i3][5] == subst1List[k3][0]:
                                                if debug:
                                                    print("final before LA 0 0", wordname[charpos], subst1List[k3][0],
                                                          subst1List[k3][2])
                                                wordname[charpos] = subst1List[k3][2]  # read subst char name from list 1
                                                if debug:
                                                    print("final after LA 0 0", wordname[charpos], subst1List[k3][0],
                                                          subst1List[k3][2])
                                                    print("final LA 0 0", word, wordname)

                                                substdone = True
                                                continue

                            if subst6List[i3][0] == '1' and subst6List[i3][1] == '0':  # two consecutive chars and one char subst
                                # print("2 seq. before subst6 ", len(subst6List[i3][4]), wordname[charpos],
                                #       subst6List[i3][3][0])
                                if wordname[charpos + 1] == subst6List[i3][3][1]:  # two chars seq. found
                                    # print("2 seq. before subst6 ", len(subst6List[i3][4]), wordname[charpos],
                                    #       subst6List[i3][3][0])
                                    for j3 in range(0, len(subst6List[i3][4])):
                                        if wordname[charpos + 2] == subst6List[i3][4][j3]:  # third word char is in list 6
                                            if debug:
                                                print("after subst6 1 0 ", (subst6List[i3][4][j3]),
                                                       wordname[charpos + 1], subst6List[i3][5])
                                            for k3 in range(0, len(subst1List)):
                                                if subst6List[i3][5] == subst1List[k3][0]:
                                                    if debug:
                                                        print("final LA 1 0 before", wordname[charpos], subst1List[k3][0],
                                                              subst1List[k3][2])
                                                    wordname[charpos] = subst1List[k3][2]  # now subst ar char postion
                                                    if debug:
                                                        print("final LA 1 0 after", wordname[charpos], subst1List[k3][0],
                                                              subst1List[k3][2])
                                                        print("final LA 1 0", word, wordname)

                                                    substdone = True
                                                    continue

                #type 6 BT substitution
                for i3 in range(0, len(subst6BTList)):
                    if not lookuptype6:
                        continue  # skip type 6
                    # print("subst6 ", wordname[charpos], subst6List[i3][0][0])
                    for i4 in range(0, len(subst6BTList[i3][3])):
                        if wordname[charpos] == subst6BTList[i3][3][i4]:  # current word char in BT list
                            # print("before subst6 ", len(subst6List[i3][4]), wordname[charpos], subst6List[i3][3][0])
                            if subst6BTList[i3][0] == '0' and subst6BTList[i3][1] == '0':
                                # print("before subst6 ", len(subst6List[i3][4]), wordname[charpos], subst6List[i3][3][0])
                                for j3 in range(0, len(subst6BTList[i3][4])):
                                    if wordname[charpos - 1] == subst6BTList[i3][4][j3]:  # check if previous char is BT list
                                        if debug:
                                            print("after subst6BT 0 0 ", (subst6BTList[i3][4][j3]),
                                                  wordname[charpos - 1], subst6BTList[i3][5])
                                        for k3 in range(0, len(subst1BTList)):
                                            if subst6BTList[i3][5] == subst1BTList[k3][0]:
                                                if debug:
                                                    print("final BT  0 0 before", wordname[charpos], subst1BTList[k3][0],
                                                          subst1BTList[k3][2])
                                                wordname[charpos] = subst1BTList[k3][2]
                                                if debug:
                                                    print("final BT 0 0 after", wordname[charpos], subst1BTList[k3][0],
                                                          subst1BTList[k3][2])
                                                    print("final BT 0 0", word, wordname)

                                                substdone = True
                                                continue

                            if subst6BTList[i3][0] == '1' and subst6BTList[i3][1] == '0':  # two char sequence
                                # print("2 seq. before subst6BT ", len(subst6BTList[i3][4]), wordname[charpos],
                                #       subst6BTList[i3][3][0])
                                if wordname[charpos - 1] == subst6BTList[i3][3][1]:  # prev. char in two chars seq.
                                    # print("2 seq. before subst6BT ", len(subst6BTList[i3][4]),
                                    #       wordname[charpos], subst6BTList[i3][3][0])
                                    for j3 in range(0, len(subst6BTList[i3][4])):
                                        if wordname[charpos - 2] == subst6BTList[i3][4][j3]: # check prev. to prev. char
                                            if debug:
                                                print("after subst6 1 0 ", (subst6BTList[i3][4][j3]),
                                                      wordname[charpos - 2], subst6BTList[i3][5])
                                            for k3 in range(0, len(subst1BTList)):
                                                if subst6BTList[i3][5] == subst1BTList[k3][0]:
                                                    if debug:
                                                        print("final BT 1 0 before", wordname[charpos],
                                                              subst1BTList[k3][0], subst1BTList[k3][2])
                                                    wordname[charpos] = subst1BTList[k3][2]
                                                    if debug:
                                                        print("final BT 1 0 after", wordname[charpos],
                                                              subst1BTList[k3][0], subst1BTList[k3][2])
                                                        print("final BT 1 0", word, wordname)

                                                    substdone = True
                                                    continue


            if debug:
                print("iter no. ij, no. of substs., final wordname =", ij, replace, wordname)
            # if (charpos+replace) > wordnamelen-1:  # recheck logic here!
            #     break

            if not substdone:
                   break  # break ij loop if no more subst required


        for j3 in range(0, len(wordname)):
            # now do char append
            if wordname[j3] == None:
                charAppend = ""
                continue
            elif wordname[j3] == 'LFName':
                charAppend = "\n"
            elif wordname[j3] == 'CRName':
                charAppend = "\r"
            elif wordname[j3] == 'ZWNJName':
                charAppend = ""
            elif wordname[j3] == 'ZWJName':
                charAppend = ""
            elif wordname[j3] == 'SpaceName':
                charAppend = " "
            elif wordname[j3] == 'LineBreak':
                charAppend = "u+2028"
            elif wordname[j3] == 'ParaSeparator':
                charAppend = "u+2029"
            else:
                wordID = (font2.getGlyphID(wordname[j3]))
                charAppend = "g+" + (hex(wordID)).replace("0x", "")

            finalDisp = finalDisp + charAppend
    #quit()
    #print(finalDisp)
    print('conversion done')

    textBox3.insert(INSERT, uniDisp)
    textBox2.insert(INSERT, finalDisp)

# display first text box using std font
textBox = Text(root, height=10, width=100, font=myFont)
textBox.pack(pady=10)

# display second text box using target font
textBox3 = Text(root, height=5, width=100, font=myFont)
textBox3.pack(pady=10)

# display third text box with unicode values using target font for debugging
textBox2 = Text(root, height=5, width=100, font=myFont)
textBox2.pack(pady=10)

# button clicks section
buttonCommit = Button(root, height=1, width=10, text="Convert", font=myFont,
                      command=lambda: retrieve_input())
# command=lambda: retrieve_input() >>> just means do this when i press the button
buttonCommit.pack()

buttonCommit2 = Button(root, height=1, width=10, text="Copy", font=myFont,
                       command=lambda: copy_clipboard())
# command=lambda: retrieve_input() >>> just means do this when i press the button
buttonCommit2.pack()

buttonCommit3 = Button(root, height=1, width=10, text="Clear", font=myFont,
                       command=lambda: clear_all())
# command=lambda: retrieve_input() >>> just means do this when i press the button
buttonCommit3.pack()

mainloop()




