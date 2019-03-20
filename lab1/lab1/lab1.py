
#install spacy
#install wikipedia

import spacy
nlp = spacy.load('en_core_web_md')
from spacy import displacy
import wikipedia
from numpy import dot
from numpy.linalg import norm

print('Text to analyze: ')
text = (u'Estonia is a country in Northern Europe. It is bordered to the north by the Gulf of Finland with Finland on the other side, to the west by the Baltic Sea with Sweden on the other side')
#text = """But Google is starting from behind. The company made a late push into hardware, and Apple’s Siri, available on iPhones, and Amazon’s Alexa software, which runs on its Echo and Dot devices, have clear leads in consumer adoption."""


print(text)
print('\n')
doc = nlp(text)

#Tokenize
print('Tokens', [t.text for t in doc]) 
print('\n')

#Find entities

#For Example:
#ORG	Companies, agencies, institutions, etc.
#GPE	Countries, cities, states.
#LOC	Non-GPE locations, mountain ranges, bodies of water.

print('Entities', [(e.text, e.label_) for e in doc.ents])
print('\n')


#Linguistic parsing

#Text: Sxna
#Lemma: Sxna baas
#POS: Part-of-speech tag... PROPN-Noun-nimisxna, verb-tegusxna, determiner, ADP-conjunction-sidesxna, ADJ-adjective-omadussxna.. jne
#Tag: Detailnepart-of-speech tag. NNP-singular, NNPS-plural,  ainsus/mitmus
#Dep: Tokenite vaheline sõltuvus
#Shape: Sxna kuju ja punktuatsioon

for token in doc:
    print('{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}'.format(token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.shape_))

#Match entity with wikipedia

#NB Wikipedia recognise the following entities PER, LOC, ORG, MISC
#Hangling exception when more than 1 result found

entities = []
print('\n')
for entity in doc.ents:
    entities.append(entity.text)
    try:
        wiki = wikipedia.page(entity.text)
        print('{:<20}\t{}\t{}'.format(entity.text, entity.label_, wiki.url))
    except wikipedia.exceptions.DisambiguationError as e:
        print("Exception.. more than one result found..")
        print(e.options)


print('\n')
#wordstr = (u'Google').lower()
wordstr = entities[0].lower()
word = nlp.vocab[wordstr]
# cosine similarity
cosine = lambda v1, v2: dot(v1, v2) / (norm(v1) * norm(v2))

# gather all known words, take only the lowercased versions
allWords = list({w for w in nlp.vocab if w.has_vector and w.orth_.islower() and w.lower_ != wordstr})

# sort by similarity
allWords.sort(key=lambda w: cosine(w.vector, word.vector))
allWords.reverse()
print("Top 10 most similar words to '"+wordstr+"':")
for word in allWords[:10]:
    print(word.orth_)

#browseris localhost:5000
displacy.serve(doc, style='ent')