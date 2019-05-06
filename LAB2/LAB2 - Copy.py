from pyswip import Prolog
import spacy
from spacy import displacy
import textacy.extract
import textacy.constants
import textacy.keyterms
from ordered_set import OrderedSet
import neuralcoref
import wikipedia
import os
import re

nlp = spacy.load('en_core_web_sm')
neuralcoref.add_to_pipe(nlp)

proxies = {
    'http': 'kn.proxy.int.kn:80',
    'https': 'kn.proxy.int.kn:80',
}
os.environ["HTTP_PROXY"]=proxies['http']
os.environ["HTTPS_PROXY"]=proxies['https']

#input_topic = input("Enter your topic: ")
#try:
#    topic = wikipedia.summary(input_topic)
#except wikipedia.exceptions.DisambiguationError as e:
#    print(e.options)
#
#cont = nlp(topic)
#topicdoc = [sent.string.strip() for sent in cont.sents]
#intext = ''.join(map(str, topicdoc[:5]))

#f=open('text2.txt','r', encoding='utf-8', errors = 'ignore')
#intex33t=f.read()

#intext1="John is a father of Andrew. Andrew is a man. Who is the father of Andrew?"


intext = """Barrack Obama was born in Hawaii in the year 1961. He was president of the United States. London is the capital and most populous city of England and the United Kingdom. 
Standing on the River Thames in the south east of the island of Great Britain, London has been a major settlement for two millennia. 
It was founded by the Romans, who named it Londinium.
"""




reasonerlist = OrderedSet()

def makefact(lst):
  if not lst: return ""
  s=""
  for el in lst[1:]:    
    if s: s+=","
    s+=el
  s=lst[0].lower()+"("+s.lower()+")" 
  print("Fact: "+s)
  return s

def extract_relations(doc):

    spans = list(doc.ents) + list(doc.noun_chunks)
    for span in spans:
        span.merge()
    
    triples = []
    


    for ent in doc.ents:
        head = ent.root.head
        chil = ent.root.head.children
        preps = []
        for prep in ent.root.head.children:
            if(prep.dep_ == "prep"):
                preps.append(prep)
        for prep in preps:
            for child in prep.children:

                triple = '{}({}, {})'.format(ent.root.head, ent.text, child.text)
                print(triple)
                triples.append(triple)
                if(child.ent_type_ == "DATE" and hasNumbers(child.text)):
                    tempchild = re.findall('\d+', child.text)[0]
                    triple = '{}({}, {})'.format(ent.root.head, ent.text, tempchild)
                    print("Converted digit: " +triple)
                
            
    
    return triples

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def parsesentence(sentence):
    sentenceDoc = nlp(sentence)
    pattern = textacy.constants.POS_REGEX_PATTERNS
    #textacy.extract.named_entities(doc, drop_determiners=True)
    #regexchunks =textacy.keyterms.key_terms_from_semantic_network(doc)
    #regexchunks =textacy.extract.noun_chunks(sentenceDoc, drop_determiners=True)
    #regexchunks = textacy.extract.pos_regex_matches(sentenceDoc, pattern['en']['VP'])
    for regexchunk in regexchunks:
        print("Pattern match: "+str(regexchunk))

    relations = extract_relations(sentenceDoc)

    print("Parsing sentence to triplets...")
    triplets = textacy.extract.subject_verb_object_triples(sentenceDoc)
    for t in triplets:
        print("triplet: "+str(t))
        token = t[0]
        tempsubj = str(t[0])

        rawfact = [str(t[2]).replace("'s ", "").replace(" ","_"), str(tempsubj).replace("'s ", "").replace(" ","_")]
        reasonerlist.add(makefact(rawfact))

#    entityset = []
#    for entity in sentenceDoc.ents:
#        print(f"{entity.text} ({entity.label_})")
#        entityset.append(entity.text)
    

    print("Parsing statements from sentences...")
    for ent in sentenceDoc.ents:
        print("Entity: "+str(ent))
        statements = textacy.extract.semistructured_statements(sentenceDoc, ent.text)
        for statement in statements:
            subject, verb, fact = statement
            print(">>sub: "+str(subject))
            print(">>verb: "+str(verb))
            print(">>fact: "+str(fact))
            tempfact = nlp(str(fact))
            chunks = tempfact.noun_chunks
            temparg = ""
            for chunk in chunks:
                if (str(chunk).startswith("the ") or str(chunk).startswith("a ")):
                    newchunk = chunk.lemma_.partition(' ')[2]
                    rawfact = [str(newchunk).replace("'s ", "").replace(" ","_"), str(subject)]
                    reasonerlist.add(makefact(rawfact))
                    temparg = str(newchunk).replace("'s ", "").replace(" ","_")
                if (chunk.root.head.text=="of" or chunk.root.head.text=="for"):
                    rawfact = [temparg, str(subject), str(chunk).replace("'s ", "").replace(" ","_")]
                    reasonerlist.add(makefact(rawfact))

            for token in chunks:
                if (str(token).startswith("the ") or str(token).startswith("a ")):
                    newtoken = token.lemma_.partition(' ')[2]
                    templist = [str(newtoken).replace("'s ", "").replace(" ","_"), str(subject)]
                else:
                    templist = [str(token.lemma_).replace("'s ", "").replace(" ","_"), str(subject)]
                reasonerlist.add(makefact(templist))

            for token in tempfact:
                if(token.pos_ == "VERB"):
                    templist = [str(token.text), str(subject)]
                    reasonerlist.add(makefact(templist))


doc = nlp(intext)
tempdoc = ""
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

print("Splitting text in senteces...")
sentences = [sent.string.strip() for sent in doc.sents]

for sentence in sentences:
    print("--------------------------------------------------------------------------------")
    print(">>Sentence: "+sentence)
    parsesentence(sentence)
    
    print("")
    print("****")

#reasonerlist.remove("")
print("")
print("Final list of facts")
print(reasonerlist)
  
print("Populating prolog dataset...")



prolog = Prolog()

for fact in reasonerlist:
    print(fact)
    prolog.assertz(str(fact))




print("Type 'quit' to finish")
input_text = ""
while(input_text != 'quit'):
    asked = ""
    reasonerlist = OrderedSet()
    input_text = input("Enter your question: ")
    if(input_text[-1]=="?"):
        if(input_text.lower().startswith("is ")):
            input_text = input_text[3:]
        else:
            tempstr = input_text.lower().partition('is ')
            input_text = "Temp is "+tempstr[-1].replace("?",".")


    
    parsesentence(input_text)

    if(len(reasonerlist)>0):
        asked = reasonerlist[-1]
    if("temp" in asked):
        asked = asked.replace("temp", "X")
    print("Asked: ")
    print(asked)
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
