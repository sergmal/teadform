#install spacy
#install wikipedia

import spacy
nlp = spacy.load('en_core_web_sm')
from spacy import displacy
import wikipedia

text = (u'Estonia is a country in Northern Europe. It is bordered to the north by the Gulf of Finland with Finland on the other side, to the west by the Baltic Sea with Sweden on the other side')

doc = nlp(text)

# Find named entities, phrases and concepts
for entity in doc.ents:
    print(entity.text, entity.label_)
    wiki = wikipedia.page(entity.text)
    print(wiki.url)

#ava oma browseris localhost:5000
displacy.serve(doc, style='ent')