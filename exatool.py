from bs4 import BeautifulSoup as soup
import requests as req
import PyPDF2
from io import BytesIO
from matplotlib.pyplot import figure
import os
import re
import sys
import numpy as np
from matplotlib import pyplot as plt
import urllib.request as ul
import pandas as pd
import itertools

#change into the desired directory to store the results of the sorting
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

def sci(keywords):    
    #initialization of variables
    keywords = ['NULL'] + keywords
    dico_keywords = {i:0 for i in keywords}
    
    #Opens the document outputed from link_retriever.py
    with open('Results.txt', 'r', encoding='utf-8') as F:
        F = F.readlines()
        limite = len(F)
    
    #Opens output file
    Searched_material = open('Searched_material.txt', 'w', encoding='utf-8')
    count_bad_links = 0
    number = 0

    #loop through each lines of the file with a link in each
    for index, i in enumerate(F): 
        #process the line to obtain a viable DOI
        i = i.strip('\n')
        i = i.split('\t')

        #indicates progression of the program
        print(f"{np.round((index/limite)*100, 2)}%")
                
        #rebuild the link to the full article
        link = 'https://doi.org/' + i[0]
        date = i[1]
        
        #retrieve data through the DOI. If an error occurs, we switch to the next article
        try :
            retrieved_data = req.get(link)
            my_raw_data = retrieved_data.content
        except Exception:
            count_bad_links +=1
            continue
        
        output = ''
        #if the DOI redirect toward a PDF, the text is extracted from it in this code
        if b'%PDF' in my_raw_data:
            data = BytesIO(my_raw_data)
            try :
                read_pdf = PyPDF2.PdfReader(data)
                for page in range(len(read_pdf.pages)):
                    txt = read_pdf.pages[page].extract_text()
                    txt = txt.encode('UTF-8', errors = 'ignore')
                    output = str(txt.strip())                
            except Exception:
                pass
        
        #filter the CSS and html beacons out of the file             
        else:
            db_txt = soup(my_raw_data, "html.parser")
            txt = db_txt.find_all(string = True)
            blacklist = [
                '[document]',
                'noscript',
                'header',
                'html',
                'meta',
                'head', 
                'input',
                'script',
                'footer',
                'style',
                ]

            for t in txt:
                if t.parent.name not in blacklist:
                    output += '{}'.format(t)

            if len(output) < 1000:
                count_bad_links+=1
                continue
            else:
                number+=1                
            
            output = re.sub("\n|\r|\rn", '', output) 
            output = output[output.find('Abstract'):].lower()
            try : 
                output = str(output[:max([m.start() for m in re.finditer('references', output)])])
            except : 
                output = str(output)      
                        
        #write the link in the output document if the conditions are fullfilled : if it is exactly the desired material.        
        dico = {keywords[i]:output.count(keywords[i].lower()) for i in range(0, len(keywords))}
        dico_keywords[max(dico, key=dico.get)] += 1
        Searched_material.write(link + '\t' + date + '\t' + str(max(dico, key=dico.get)) + '\n')
        dico = {}
                
    for key, res in dico_keywords.items():
        print(key, res)

    #Summarize the results in the console to give a preview of the results
    print(f'full text retrieved : {number}\t impossible links to retrieve : {count_bad_links}')
    return 'Done'

#print(sci(["Illumina", "Nanopore"]))

def tendency(keywords):
    #open results files
    results = open('Searched_material.txt', 'r', encoding='utf-8')

    #Process the data in list containing only the date in which the articles were written
    list_material_date = [(i.split('\t')[1].strip('\n'),i.split('\t')[2].strip('\n')) for i in results.readlines()]

    #Initialize the dates to position the temporality of the articles
    dates = [date for date in range(min([int(elt[0]) for elt in list_material_date]), max([int(elt[0]) for elt in list_material_date]))]
    
    #Count each date occurence as each article has an associated publication date. Thus number of date = number of articles
    count_dates = {i:[int(j[0]) for j in list_material_date if j[1] == i] for i in keywords}

    dec = 0
    fig = figure(figsize=(11, 5))
    for i in count_dates:
        res = [count_dates[i].count(j) for j in dates]
        dates = [i+dec for i in dates]
        plt.bar(dates, res, label=i, width = 0.4, alpha=0.2)
        plt.xlabel('time')
        plt.ylabel('number of publications')
        plt.title(f'Global distribution of the publications between {min(dates)} and {max(dates)}')

    
    plt.legend()
    plt.savefig('plot.png')
    results.close()

#tendency(['virus', 'prokaryote', 'eukaryote'])

def dl_intel(url):  
    #get HTML data
    client = req.get(url)
    htmldata = client.text
    client.close()    

    #Locate the desired data : here we want to filter out the reviews 
    db = soup(htmldata, "html.parser")
    locator = db.findAll('span', {'class':'docsum-journal-citation full-journal-citation'})  
    locator_review = db.findAll('div', {'class':'docsum-content'})  
        
    base = str(locator_review).split("docsum-content")
    del base[0]
    locator = str(locator).split('</span>')
    del locator[-1]

    #les index correspondent 
    is_review = [index for index, val in enumerate(base) if "Review" in val]
    is_review += [index for index, val in enumerate(base) if "doi:" not in val]

    for index in sorted(is_review, reverse=True):
        del locator[index]

    locator = ' KODE '.join(locator) + ' '

    doi_list = re.findall('doi: (.*?)(?=.<|. )', str(locator))
    locator = re.sub(';(.*?)(?=.<|<)', "", locator)
    locator = re.sub(";.*", "", locator)
    date_list = re.findall(' \d{4} ', locator)

    assert(len(doi_list) == len(date_list))
    
    intel = [f"{doi_list[i]}\t{date_list[i].strip(' ')}\n" for i in range(0, len(doi_list))]

    return intel

dl_intel(f"https://pubmed.ncbi.nlm.nih.gov/?term=nanopore+sequencing&filter=simsearch2.ffrft&filter=years.2014-2024&size=200&page=2")

#This function's sole purpose is to pass to the next page in PubMed. It is possible to set a limit to how many pages you want to collect the articles' link from.
def switch_page(url):
    #find the limit number of pages to go through
    client = req.get(url)
    htmldata = client.text
    client.close()
    db = soup(htmldata, "html.parser")
    locator = db.findAll('span', {'class':'value'})  

    nb_articles = ''.join(re.findall('[0-9]+', str(locator[0])))
    print(nb_articles)
    limite = (int(nb_articles)//200)+1
    if limite > 30:
        limite = 5
    count = 1
    link = url
    
    #Open our definitive file
    Results = open('Results.txt', 'w')
    
    while count <= limite :
        link = url + '&page=' + str(count)
        K=dl_intel(link)
        print(f"{np.round((count/limite)*100)}%")
        count+=1
        for lines in K:
            Results.write(lines)
    print(f'{limite} articles retrieved !\n')
    return ''

if __name__ == "__main__":
    keywords = list(' '.join(sys.argv[3:]).split())    
    print(keywords)
    url = str(sys.argv[2])
    dir_output = str(sys.argv[1])
    pure_url = 'https://pubmed.ncbi.nlm.nih.gov/'
    
    os.chdir(dir_output)
    switch_page(url)
    print('Articles retrieved successfully, beginning sorting...')
    try :
        sci(keywords)
    except Exception:
        pass
    print('Sorting done, preparig visual representation')
    tendency(keywords)
    print('Figure is ready')
