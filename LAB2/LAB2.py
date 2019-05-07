from pyswip import Prolog
import spacy
import textacy.extract
import textacy.constants
import textacy.keyterms
from ordered_set import OrderedSet
import neuralcoref
import re
import temp

nlp = spacy.load('en_core_web_md')
neuralcoref.add_to_pipe(nlp)


intext = """John is a father of Andrew. Andrew is a man. Andrew is very smart. Andrew is a father of Bill. Tom is a cat. All cats are cool and nice. Barack Obama was born in Hawaii in 1961. He was president of the United States. London is the capital and most populous city of England. 
Standing on the River Thames in the south east of the island of Great Britain, London has been a major settlement for two millennia. It was founded by the Romans, who named it Londinium.
"""

print(intext)
reasonerlist = OrderedSet()
reasonerlistRules = OrderedSet()


def makefact(lst):
  if not lst: return ""
  s=""
  for el in lst[1:]:    
    if s: s+=","
    s+=el
  s=lst[0].replace("'s ", "").replace(" ","_").lower()+"("+s.replace("'s ", "").replace(" ","_").lower()+")" 
  #print("Fact: "+s)
  return s

def rm(txt):
    if (str(txt).lower().startswith("the ") or str(txt).lower().startswith("a ")):
        return txt.partition(' ')[2].replace("'s ", "").replace(" ","_").lower()
    return txt.replace("'s ", "").replace(" ","_").lower()

def isNegative(tok):
    negatives = { "no", "not", "n't", "never", "none" }
    for dep in list(tok.lefts)+list(tok.rights):
        if dep.lower_ in negatives:
            return True
    return False


def extract_relations1(doc):
    spans = list(doc.ents) + list(doc.noun_chunks)
    for span in spans:
        span.merge()

    for ent in doc.ents:
        preps = []
        for prep in ent.root.head.children:
            if(prep.dep_ == "prep"):
                preps.append(prep)
        for prep in preps:
            for child in prep.children:
                triple = '{}({},{})'.format(rm(ent.root.head.text), rm(ent.text), rm(child.text))
                reasonerlist.add(triple)
                if(child.ent_type_ == "DATE" and hasNumbers(child.text)):
                    tempchild = re.findall('\d+', child.text)[0]
                    triple = '{}({},{})'.format(rm(ent.root.head.text), rm(ent.text), rm(tempchild))
                    reasonerlist.add(triple)

def extract_relations2(doc):  

    tupl = []
    for chunk in doc.noun_chunks:
         #print(chunk.text)

         if(chunk.root.dep_ == "nsubj" or chunk.root.dep_ == "nsubjpass"):
            tupl.append(chunk)
         if(chunk.root.dep_ == "attr"):
            tupl.append(chunk)
         if(chunk.root.dep_ == "pobj"):
            tupl.append(chunk)
         if(chunk.root.dep_ == "cobj" and chunk.root.head.text == pobj.root.text):
            tupl.append(chunk)

         if(len(tupl) == 2):
            triple = '{}({})'.format(rm(tupl[1].text), rm(tupl[0].text))
            #print(triple)
            reasonerlist.add(triple)
            tupl = []
         if(len(tupl) == 3):
            triple = '{}({},{})'.format(rm(tupl[1].text), rm(tupl[0].text), rm(tupl[2].text))
            #print(triple)
            reasonerlist.add(triple)
            tupl = []
         if(len(tupl) == 4):
            triple = '{}({},{})'.format(rm(tupl[1].text), rm(tupl[0].text), rm(tupl[2].text))
            #print(triple)
            reasonerlist.add(triple)
            triple = '{}({},{})'.format(rm(tupl[1].text), rm(tupl[0].text), rm(tupl[3].text))
            #print(triple)
            reasonerlist.add(triple)
            tupl = []
    
def extract_relations3(doc):  

    tupl = []
    for tok in doc:
         #print(chunk.text)

         if(tok.dep_ == "nsubj" or tok.dep_ == "nsubjpass"):
            tupl.append(tok)
         if(tok.dep_ == "ROOT" and tok.head.pos_ == "VERB"):
            for child in tok.rights:
                if(len(tupl)!=0 and child.text != tupl[0].text and child.dep_ != "punct"):
                    tupl.append(child) 
                    for chi in child.rights:
                        if(chi.dep_ == "conj" and chi.head.text == child.text):
                            tupl.append(chi) 

         if(len(tupl) == 2):
            triple = '{}({})'.format(rm(tupl[1].lemma_), rm(tupl[0].lemma_))
            reasonerlist.add(triple)
            tupl = []

         if(len(tupl) == 3):
            triple = '{}({})'.format(rm(tupl[1].lemma_), rm(tupl[0].lemma_))
            reasonerlist.add(triple)
            triple = '{}({})'.format(rm(tupl[2].lemma_), rm(tupl[0].lemma_))
            reasonerlist.add(triple)
            tupl = []

def extract_relations4rule(doc):  

    tupl = []
    for tok in doc:
         #print(chunk.text)
         det = ['all', 'every'];
         if(tok.dep_ == "det" and tok.head.pos_ == "NOUN" and tok.text.lower() in det):
            tupl.append("X")
         if(len(tupl)!=0 and tok.dep_ == "nsubj"):
            tupl.append(tok)
         if(len(tupl)!=0 and tok.dep_ == "ROOT" and tok.head.pos_ == "VERB"):
            for child in tok.rights:
                if(tupl[1].dep_ == "nsubj" and child.text != tupl[1].text and child.dep_ != "punct"):
                    tupl.append(child) 
                    for chi in child.rights:
                        if(chi.dep_ == "conj" and chi.head.text == child.text):
                            tupl.append(chi) 

         if(len(tupl) == 3):
            triple = '{}(X):-{}(X)'.format(rm(tupl[2].lemma_), rm(tupl[1].lemma_))
            reasonerlistRules.add(triple)
            tupl = []

         if(len(tupl) == 4):
            triple = '{}(X):-{}(X)'.format(rm(tupl[2].lemma_), rm(tupl[1].lemma_))
            reasonerlistRules.add(triple)
            triple = '{}(X):-{}(X)'.format(rm(tupl[3].lemma_), rm(tupl[1].lemma_))
            reasonerlistRules.add(triple)
            tupl = []

def extract_relations5(doc):
    triplets = textacy.extract.subject_verb_object_triples(doc)
    for t in triplets:
        #print("triplet: "+str(t))
        token = t[0]
        tempsubj = rm(str(t[0]))

        rawfact = [rm(str(t[2])).replace("'s ", "").replace(" ","_"), rm(str(tempsubj)).replace("'s ", "").replace(" ","_")]
        reasonerlist.add(makefact(rawfact))

def extract_relations6(doc):
    #print("Parsing statements from sentences...")
    for ent in doc.ents:
        #print("Entity: "+str(ent))
        for token in doc:
            if(token.pos_ == "VERB"):
                statements = textacy.extract.semistructured_statements(doc, ent.text, cue = token.lemma_)
                for statement in statements:
                    subject, verb, fact = statement
                    #print(">>sub: "+str(subject))
                    #print(">>verb: "+str(verb))
                    #print(">>fact: "+str(fact))
                    tempfact = nlp(str(fact))
                    chunks = tempfact.noun_chunks
                    temparg = ""
                    for chunk in chunks:
                      if (str(chunk).startswith("the ") or str(chunk).startswith("a ")):
                          newchunk = chunk.lemma_.partition(' ')[2]
                          rawfact = [str(newchunk), str(subject)]
                          reasonerlist.add(makefact(rawfact))
                          temparg = str(newchunk)
                      if (chunk.root.head.text=="of" or chunk.root.head.text=="for"):
                          rawfact = [temparg, str(subject), str(chunk)]
                          reasonerlist.add(makefact(rawfact))
    
                    for token in chunks:
                      if (str(token).startswith("the ") or str(token).startswith("a ")):
                          newtoken = token.lemma_.partition(' ')[2]
                          templist = [str(newtoken), str(subject)]
                      else:
                          templist = [str(token.lemma_), str(subject)]
                          reasonerlist.add(makefact(templist))

                    for token in tempfact:
                      if(token.pos_ == "VERB"):
                        templist = [str(token.text), str(subject)]
                        reasonerlist.add(makefact(templist))


def extract_relations7(doc):
    tupl = []
    tupl2 = []
    for tok in doc:
        if(tok.pos_ == "ADP"):
            for token in doc:
                if(token.dep_ == "ROOT"):
                    for child in token.children:
                        if(child.dep_ == "attr"):
                            tupl.append(child)
                            for chi in child.children:
                                if(chi.dep_ == "prep"):
                                    for c in chi.children:
                                        if(c.dep_ == "pobj"):
                                            tupl.append(c)
                    for child in token.children:
                        if(child.dep_ == "nsubj" or child.dep_ == "pobj"):
                            tupl.append(child)
                            tupl2.append(child)


                            
            if(len(tupl) == 3):
                triple = '{}({},{})'.format(rm(tupl[0].text), rm(tupl[2].text), rm(tupl[1].text))
                #print(triple)
                reasonerlist.add(triple)
                tupl = []

            if(len(tupl) == 2):
                triple = '{}({})'.format(rm(tupl[0].text), rm(tupl[1].text))
                #print(triple)
                reasonerlist.add(triple)
                tupl = []


def extract_relations8(doc):
    tupl = []
    for token in doc:
        if(token.dep_ == "ROOT" and token.head.pos_ == "VERB" and token.tag_ != "VBZ"):
            tupl.append(token)
            for child in token.children:
                if(child.dep_ == "nsubjpass" or child.dep_ == "nsubj"):
                    tupl.append(child)
                if(child.dep_ == "agent" or child.dep_ == "prep"):
                    for chi in child.children:
                        if(chi.dep_ == "pobj"):
                            tupl.append(chi)


        if(len(tupl) == 4):
            triple = '{}({},{})'.format(rm(tupl[0].text), rm(tupl[1].text), rm(tupl[2].text))
            #print(triple)
            reasonerlist.add(triple)
            triple = '{}({},{})'.format(rm(tupl[0].text), rm(tupl[1].text), rm(tupl[3].text))
            #print(triple)
            reasonerlist.add(triple)
            tupl = []                           
        if(len(tupl) == 3):
            triple = '{}({},{})'.format(rm(tupl[0].text), rm(tupl[1].text), rm(tupl[2].text))
            #print(triple)
            reasonerlist.add(triple)
            tupl = []

def extract_relations9(doc):
    tupl = []
    for token in doc:
        if(token.dep_ == "ROOT" and token.head.pos_ == "PROPN"):
            tupl.append(token)
            for child in token.children:
                if(child.head.pos_ == "PROPN"):
                    tupl.append(child)
                    for chi in child.children:
                        if(chi.dep_ == "agent"):
                            for chi in child.children:
                                if(chi.dep_ == "pobj"):
                                    tupl.append(chi)


                            
        if(len(tupl) == 3):
            triple = '{}({},{})'.format(rm(tupl[0].text), rm(tupl[1].text), rm(tupl[2].text))
            #print(triple)
            reasonerlist.add(triple)
            tupl = []

def extract_relations10(doc):
    tupl = []
    for token in doc:
        if(token.dep_ == "ROOT" and token.head.pos_ == "VERB" and token.tag_ != "VBN"):
            tupl.append(token)
            for child in token.children:
                if(child.head.pos_ == "PROPN"):
                    tupl.append(child)
                    for chi in child.children:
                        if(chi.dep_ == "agent"):
                            for chi in child.children:
                                if(chi.dep_ == "pobj"):
                                    tupl.append(chi)


                            
        if(len(tupl) == 3):
            triple = '{}({},{})'.format(rm(tupl[0].text), rm(tupl[1].text), rm(tupl[2].text))
            #print(triple)
            reasonerlist.add(triple)
            tupl = []

def extract_relations10(doc):
    tupl2 = []
    for tok in doc:
        if(tok.pos_ == "ADP"):
            for token in doc:
                if(token.dep_ == "ROOT"):
                    for child in token.children:
                        if(child.pos_ == "VERB" and child.tag_ != "VBZ" and child.tag_ != "VBN"):
                            tupl2.append(child)
                            for chi in child.children:
                                if(chi.dep_ == "prep"):
                                    for c in chi.children:
                                        if(c.dep_ == "pobj"):
                                            tupl2.append(c)
                    for child in token.children:
                        if(child.dep_ == "nsubj" or child.dep_ == "pobj"):
                            tupl2.append(child)                  

            if(len(tupl2) == 4):
                triple = '{}({},{})'.format(rm(tupl2[0].text), rm(tupl2[3].text), rm(tupl2[1].text))
                #print(triple)
                reasonerlist.add(triple)
                triple = '{}({},{})'.format(rm(tupl2[0].text), rm(tupl2[3].text), rm(tupl2[2].text))
                #print(triple)
                reasonerlist.add(triple)
                tupl = []

            if(len(tupl2) == 3):
                triple = '{}({},{})'.format(rm(tupl2[0].text), rm(tupl2[2].text), rm(tupl2[1].text))
                #print(triple)
                reasonerlist.add(triple)
                tupl = []

            if(len(tupl2) == 2):
                triple = '{}({})'.format(rm(tupl2[0].text), rm(tupl2[1].text))
                #print(triple)
                reasonerlist.add(triple)
                tupl = []

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def parsesentence(sentence):
    sentenceDoc = nlp(sentence)
    extract_relations1(sentenceDoc)

    sentenceDoc2 = nlp(sentence)


    extract_relations2(sentenceDoc2)
    #print(reasonerlist)

    extract_relations3(sentenceDoc2)
    #print(reasonerlist)

    extract_relations4rule(sentenceDoc2)
    #print(reasonerlist)

    extract_relations5(sentenceDoc2)
    #print(reasonerlist)

    extract_relations6(sentenceDoc2)
    #print(reasonerlist)

    extract_relations7(sentenceDoc2)
    #print(reasonerlist)

    extract_relations8(sentenceDoc2)
    #print(reasonerlist)

    extract_relations9(sentenceDoc2)
    #print(reasonerlist)

    extract_relations10(sentenceDoc2)
    #print(reasonerlist)

    svos = temp.findSVOs(sentenceDoc2)
    #print("SVOS:")
    #print(svos)


doc = nlp(intext)

tempdoc = ""
print("Coreference parsing..")
for token in doc:
    if token.pos_ == 'PRON' and token._.in_coref:
        for cluster in token._.coref_clusters:
            temptok = str(token.text) 
            tempclust = str(cluster.main.text)
            
            print(token.text + " => " + cluster.main.text)
        tempdoc=tempdoc+cluster.main.text
        tempdoc=tempdoc+ " "
    else:
        tempdoc=tempdoc + token.text
        tempdoc=tempdoc + " "
doc = nlp(tempdoc)

#print("Splitting text in senteces...")
sentences = [sent.string.strip() for sent in doc.sents]

for sentence in sentences:
    #print("--------------------------------------------------------------------------------")
    #print(">>Sentence: "+sentence)
    parsesentence(sentence)
    #print("****")

print("")

print("Populating prolog dataset...")



prolog = Prolog()
print("Final list of facts")

determinersForSimilarity = OrderedSet()

for fact in reasonerlist:
    print(fact)
    excractFirstWord = fact.partition('(')[0]
    determinersForSimilarity.append(excractFirstWord)
    prolog.assertz(fact)

for rule in reasonerlistRules:
    print(rule)
    prolog.assertz(rule)



print("Type 'quit' to finish")
input_text = ""

similaritiestable = []

def parsequestion(quest):
    if(quest.startswith("Is ")):
        quest = quest[3:].replace("?",".")
    elif("was" in quest):
        tempstr = quest.partition('was ')
        quest = "Echo was "+tempstr[-1].replace("?",".")
    else:
        tempstr = quest.partition('is ')
        quest = "Echo is "+tempstr[-1].replace("?",".")

    parsesentence(quest)
    asked = ""
    if(len(reasonerlist)>0):
        asked = reasonerlist[-1]
        if("echo" in asked):
            asked = asked.replace("echo", "X")
    return asked

while(input_text != 'quit'):
    asked = ""
    reasonerlist = OrderedSet()
    print("")
    input_text = input("Enter your question: ")
    if(input_text[-1]=="?"):

        
        asked = parsequestion(input_text)
        print("Asked: ")
        print(asked)
        extractFirstWord = asked.partition('(')[0]
        askedDoc = nlp(extractFirstWord)
        if(asked != "" and extractFirstWord not in determinersForSimilarity and askedDoc[0].pos_ == "ADJ"):
            for word in determinersForSimilarity:
                wordDoc = nlp(word)
                if(wordDoc[0].has_vector):
                    similaritiestable.append([word, askedDoc[0].similarity(wordDoc[0])])

            similaritiestable.sort(key=lambda x: float(x[1]), reverse = True)
            for t in similaritiestable:
                print(t)
            bestval = similaritiestable[0]
            askedFull = input_text.replace(extractFirstWord,bestval[0])
            print("Did you mean: "+ askedFull)
            asked = parsequestion(askedFull)
            similaritiestable = []
        try:
            result = "No"
            for s in prolog.query(asked):
        
                if not s:
                    result = "Yes"
                    break
                else:   
                    result = s["X"]
                    break

            print(result)
        except Exception as e:
            #print(e)
            print("Sorry, I dont understand your question..")
