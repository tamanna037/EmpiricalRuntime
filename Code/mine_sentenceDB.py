import pandas as pd
from github_token import *
import spacy
import nltk
import re
from nltk.corpus import stopwords
from spacy.language import Language
from string import punctuation
from nltk.corpus import stopwords
from spacy.lang.en import English
import warnings
warnings. simplefilter(action='ignore', category=FutureWarning)
import datetime
sentDictList=[]
import requests
import os
issueno=0
nltk.download('stopwords')
stopwords = set(stopwords.words("english"))

nlp = spacy.load("en_core_web_sm")

codes = "([\u0060]{3}([\s\S]*)[\u0060]{3})"
reply = "^[> ]([\s\S]*?)(\r\n)"

#sample_src = 'runtime TitleBodyDB.csv'
sample_src='runtime sampleDB.csv'
#sample_src='runtime_commentinline_predictions.csv'
#output_src='runtime_cmnt_sentence.csv'
#output_src= 'runtime titlebodyinline.csv'

codePattern = "([\u0060]{3}([^\u0060]*)[\u0060]{3})"
codePattern2="([\u0060]{1}([^\u0060]*)[\u0060]{1})"

parser = English()
stop_words = list(punctuation) + ["'s","'m","n't","'re","-","'ll",'...'] #+ stopwords.words('english')
word_count = lambda sentence: len([x for x in list(map(str,parser(sentence))) if x not in stop_words])

def longest_sentence_length(sentence_list):
    return max([word_count(sentence) for sentence in sentence_list])

def processText(line):

    pattern = re.compile(
        r'[\[\(]http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+[\]\)]')

    line = re.sub(codePattern, 'CODE', line)
    line = re.sub(codePattern2, 'CODE', line)
    #if(issueno!=101):
        #line = re.sub(pattern, ' URL ', line)
    #print(line)

    return line


def removewhitespacefromcode(line):

    #print(0)
    line = re.sub(codePattern, "CODE", line)
    line = re.sub(codePattern2, "CODE", line)

    #print(line)
    return line

token = os.getenv('GITHUB_TOKEN', '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')
headers = {'Authorization': f'token {token}'}


def getSentencesFromCmnt(cmnt):
    cmnt = removewhitespacefromcode(cmnt)
    tokens = nlp(cmnt)
    newSentList = []
    s=0
    for sent in tokens.sents:
        sentF = sent.text
        sentF = sentF.strip()

        if (len(sentF) > 0):
            if (sentF[0] == ">"):
                sentF=sentF.replace(sentF[:1], '')
                sentF = sentF.strip()

        newSentList.append(sentF)
    return newSentList
def getIssuePost(issuelink):

    global threadSenCnt
    global maxThreadSenLen
    global firstTime
    global issuePoster
    threadSenCnt = 0
    maxThreadSenLen = 0

    query_url = f"https://api.github.com/repos/{ issuelink['Link'].split('/')[3]}/{ issuelink['Link'].split('/')[4]}/issues/{ issuelink['Link'].split('/')[6]}"
    r = requests.get(query_url, headers=headers)
    temp_list = r.json()  # list of dictionary

    #  region Title
    title_dict = {}
    title_dict['issue_num'] = issuelink['Link'].split('/')[6]
    title_dict['type'] = 'title'
    title_dict['state'] = temp_list['state']
    title_dict['Original Text']=temp_list['title']
    title_dict['Processed Text']=processText((temp_list['title']))

    title_dict['Full Length'] = len(title_dict['Original Text'])
    title_dict['len'] = len(title_dict['Processed Text'])

    title_dict['aa'] = temp_list['author_association']
    title_dict['begauth'] = True
    title_dict['has_code'] = False
    title_dict['first_turn'] = True
    title_dict['last_turn'] = False

    d = datetime.datetime.strptime(temp_list['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    firstTime = d.timestamp()
    title_dict['created_at'] = firstTime

    num_words=word_count(title_dict['Processed Text'])
    title_dict['clen'] = num_words
    title_dict['tlen'] =num_words

    title_dict['cloc'] = 1

    threadSenCnt = threadSenCnt + 1
    title_dict['tloc'] = threadSenCnt

    title_dict['tpos1'] = firstTime
    title_dict['tpos2'] = firstTime
    title_dict['ppau'] = 0
    title_dict['npau']=firstTime



    maxThreadSenLen = title_dict['len']
    issuePoster = temp_list['user']['login']


    # endregion


    newSentList = getSentencesFromCmnt(temp_list['body'])

    #region add title
    processedNewSentNumWord=[word_count(processText(sent)) for sent in newSentList]
    longestSenInCmnt = max(processedNewSentNumWord)
    #print(title_dict['Processed Text'])
    titleNumWord=word_count(title_dict['Processed Text'])
    if(titleNumWord>longestSenInCmnt):
        longestSenInCmnt=titleNumWord
    #print('max'+str((longestSenInCmnt)))
    #print(processedNewSentNumWord)
    #print(title_dict['clen'])
    title_dict['clen']=title_dict['clen']/longestSenInCmnt
    title_dict['cloc'] = title_dict['cloc']  / (1+len(newSentList))
    sentDictList.append(title_dict)
    #title_dict['Original Text']=""
    #title_dict['Processed Text']=""
    #print(title_dict)

    #endregion
    # keys = ['issue_number', 'Original Text','Processed Text', 'Code', 'Full Length', 'len', 'tloc',
    # 'cloc', 'tpos1', 'tpos2', 'clen', 'tlen',
    # 'ppau', 'npau', 'aa', 'begauth', 'has_code', 'first_turn', 'last_turn']
    for sentCnt in range(len(newSentList)):
        sent = newSentList[sentCnt]
        # region post
        post_dict = {}
        post_dict['issue_num'] = issuelink['Link'].split('/')[6]
        post_dict['type'] = 'body'
        post_dict['state'] = temp_list['state']
        post_dict['Original Text'] = sent
        processed_sent = processText(sent)
        post_dict['Processed Text'] = processed_sent

        post_dict['Full Length'] = len(sent)
        post_dict['len'] = len(processed_sent)

        post_dict['aa'] = temp_list['author_association']
        post_dict['begauth'] = True
        if ('CODE' in processed_sent):
            post_dict['has_code'] = True
        else:
            post_dict['has_code'] = False

        post_dict['first_turn'] = True
        post_dict['last_turn'] = False

        post_dict['created_at'] = firstTime

        num_words = word_count(post_dict['Processed Text'])
        post_dict['clen'] = num_words / longestSenInCmnt
        post_dict['tlen'] = num_words
        if (maxThreadSenLen < post_dict['len']):
            maxThreadSenLen = post_dict['len']

        post_dict['cloc'] = (sentCnt+2) / (1+len(newSentList))
        threadSenCnt = threadSenCnt + 1
        post_dict['tloc'] = threadSenCnt

        post_dict['tpos1'] = firstTime
        post_dict['tpos2'] = firstTime
        post_dict['ppau'] = 0
        post_dict['npau'] = firstTime

        sentDictList.append(post_dict)
        #post_dict['Original Text'] = ""
        #post_dict['Processed Text'] = ""
        #print(post_dict)
    return  issuelink['Link'].split('/')[6],temp_list['state']
        # endregion
def getCmntInfo(temp_list, issueid,state):
    global sentList
    global threadSenCnt
    global maxThreadSenLen
    global lastTime

    d = datetime.datetime.strptime(temp_list[len(temp_list)-1]['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    lastTime = d.timestamp()

    prevTime=firstTime
    for cmntCnt in range(len(temp_list)):
        if(cmntCnt==len(temp_list)-1):
            nextTime=0
        else:
            d = datetime.datetime.strptime(temp_list[cmntCnt+1]['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            nextTime = d.timestamp()
        #if(cmntCnt!=5):
            #continue
        dict=temp_list[cmntCnt]
        cmnt = dict['body']
        #print(cmntCnt)
        newSentList = getSentencesFromCmnt(cmnt)
        if(len(newSentList)==0):
            continue
        #maxSenInCmnt=max(newSentList, key=len)
        processedNewSentNumWord = [word_count(processText(sent)) for sent in newSentList]
        #print(newSentList)
        longestSenInCmnt = max(processedNewSentNumWord)
        if(longestSenInCmnt==0):
            longestSenInCmnt=1
        for sentCnt in range(len(newSentList)):
            sent=newSentList[sentCnt]
            sent_dict={}

            # region cmnt
            #sent_dict['issue_number'] = issue_number
            sent_dict['Original Text'] = sent
            processed_sent = processText(sent)
            sent_dict['Processed Text'] = processed_sent

            sent_dict['Full Length'] = len(sent)
            sent_dict['len'] = len(processed_sent)

            sent_dict['aa'] = dict['author_association']
            if (dict['user']['login'] == issuePoster):
                sent_dict['begauth'] = True
            else:
                sent_dict['begauth'] = False

            if ('CODE' in processed_sent):
                sent_dict['has_code'] = True
            else:
                sent_dict['has_code'] = False

            d = datetime.datetime.strptime(dict['created_at'], "%Y-%m-%dT%H:%M:%SZ")
            curTime = d.timestamp()
            sent_dict['first_turn'] = False
            if(cmntCnt==len(temp_list)-1):
                sent_dict['last_turn'] = True
            else:
                sent_dict['last_turn'] = False

            sent_dict['created_at'] = curTime

            num_word=word_count(sent_dict['Processed Text'])
            sent_dict['clen']=num_word/longestSenInCmnt
            sent_dict['tlen']=num_word
            if (maxThreadSenLen < sent_dict['len']):
                maxThreadSenLen = sent_dict['len']


            sent_dict['cloc'] = (sentCnt+1)/len(newSentList)
            threadSenCnt = threadSenCnt + 1
            sent_dict['tloc'] = threadSenCnt

            sent_dict['tpos1'] = curTime
            sent_dict['tpos2'] = curTime
            sent_dict['ppau'] = curTime-prevTime
            if(nextTime==0):
                sent_dict['npau']=nextTime
            else:
                sent_dict['npau'] = nextTime-curTime

            sent_dict['issue_num'] = issueid
            sent_dict['type'] = 'comment'
            sent_dict['state'] = state

            sentDictList.append(sent_dict)

            #sent_dict['Original Text'] = ""
            #sent_dict['Processed Text'] = ""
            #print(sent_dict)
            # endregion
        prevTime = curTime


df_repo = pd.read_csv(sample_src)
df_sen = pd.DataFrame()

row_num=0
df_append = pd.DataFrame()
for index, issuelink in df_repo.iterrows():
    issueno=index
    sentDictList = []
    print(index)
    repo_url = issuelink['Link'].split('/')[3] + '/' + issuelink['Link'].split('/')[4]
    repo = g.get_repo(repo_url)
    # print(issuelink['Link'].split('/')[6])
    issue = repo.get_issue((int)(issuelink['Link'].split('/')[6]))

    #print(repo_url)
    issueid,state=getIssuePost(issuelink)

    query_url = f"https://api.github.com/repos/{issuelink['Link'].split('/')[3]}/{issuelink['Link'].split('/')[4]}/issues/{issuelink['Link'].split('/')[6]}/comments"
    params = {
        "per_page": 100,
    }
    r = requests.get(query_url, headers=headers, params=params)
    temp_list = r.json()
    if(len(temp_list)!=0):
        d = datetime.datetime.strptime(temp_list[0]['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        nextTime = d.timestamp()
         # print(nextTime)
        for item in sentDictList:
            item['npau'] = nextTime - item['npau']
    else:
        for item in sentDictList:
            item['npau'] = 0
    if (len(temp_list) != 0):
        getCmntInfo(temp_list, issueid,state)

    df = pd.DataFrame.from_records(sentDictList)
    #print(df)
    df.tlen = df.tlen / df.tlen.max()
    df.tloc = df.tloc / df.iloc[len(df) - 1].tloc
    total_time_diff = lastTime - firstTime
    df.tpos1 = (df.tpos1 - firstTime) / total_time_diff
    df.tpos2 = (lastTime - df.tpos2) / total_time_diff
    # print(df.ppau.max())
    df.ppau = (df.ppau / df.ppau.max())
    df.npau = (df.npau / df.npau.max())
    print(len(df))
    #print(df)

    df_append = pd.concat([df_append, df], ignore_index=True)

df_append.to_csv('sentencewithstateruntime.csv')






