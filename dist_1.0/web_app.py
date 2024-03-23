import streamlit as st
import time
import os
import re
import sys
from matplotlib.pyplot import figure
import numpy as np
from matplotlib import pyplot as plt
import urllib.request as ul
import streamlit as st

#Automate the path changing to the directory where the .csv is
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

import exatool

PURE_URL = 'https://pubmed.ncbi.nlm.nih.gov/'

st.set_page_config(layout="wide")
st.header("Welcome to exatool !", divider='rainbow')
domain = '+'.join(re.findall("[A-z]+" , st.text_input("### Enter the domain you want to research")))
keywords = re.findall("[A-z]+", st.text_input("### Enter the keywords"))
date = '-'.join(re.findall("[0-9]+", st.text_input("### Enter the date range you want to research")))  
date_range = date.split('-')

st.markdown("If you found this tool useful, please cite it as : **BETTIATI M. (2024). Exatools [Python]. https://github.com/ZeepReactorr/exatools**", )

if st.button("Start research"):
    url = f"https://pubmed.ncbi.nlm.nih.gov/?term={domain}&filter=simsearch2.ffrft&filter=years.{date}"
    with st.status("Running...", expanded=True) as status:
        if st.button("stop"):
            status.update("Stopped")
            st.stop()
            
        exatool.switch_page(url, PURE_URL)
            
        exatool.sci(keywords)

        st.write("Research complete, preparing graph")
        time.sleep(1.5)
        status.update(expanded=False)

    exatool.tendency(keywords, date_range)
    st.image("plot.png", width=900)

#oxyrrhis sequencing  
#illumina nanopore 
#2010 2024
