# This script converts letters encoded in XML to LaTeX files.
# Author: gaborpalko
# TODO hi_rend regex vagy függvény

import time
import os
from bs4 import BeautifulSoup
import re


def hi_rend(soup):
    soup = str(soup).replace("\n", "")
    soup = re.sub('\s+', " ", soup)
    soup = re.sub('<hi +rend *= *"italic" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textit{\\1}\\2', soup)
    soup = re.sub('<hi +rend *= *"smallcap" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textsc{\\1}\\2', soup)
    soup = re.sub('<hi +rend *= *"bold" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textbf{\\1}\\2', soup)
    soup = BeautifulSoup(soup, "xml")
    return(soup)


def make_latex(xml, latex):
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")
        with open(latex, "w", encoding="utf8") as f_latex:

            # Insert LaTeX doc header
            with open("begin.txt", "r", encoding="utf8") as f_begin:
                begin = f_begin.read()
                f_latex.write(begin)

            # Delete <ref> tags
            for i in sp.find_all("ref"):
                i.extract()

            # Insert title
            title = str(sp.TEI.teiHeader.fileDesc.titleStmt.title.text)
            f_latex.write("\n" + "\section{" + title + "}" + "\n\n")

            # Insert manuscript description
            country = str(sp.country.text)
            settlement = str(sp.settlement.text)
            institution = str(sp.institution.text)
            repository = str(sp.repository.text)
            f_latex.write("\\begin{center}" + "\n" + "\\textit{Manuscript used}: " + country + ", " + settlement + ", "
                          + institution + ", " + repository + "\n\n")

            # Insert critintro (Notes, Photo copy)
            critIntro = sp.notesStmt.find_all("note", attrs= {"type": "critIntro"})
            for i in critIntro:
                i = hi_rend(i).text
                i = str(i).replace("\n", "")
                f_latex.write(i + "\n\n")

            # Insert publication
            publication = sp.notesStmt.find("note", attrs={"type": "publication"})
            publication = hi_rend(publication)
            f_latex.write(str(publication.text) + "\n\n")

            # Insert translation
            translation = sp.notesStmt.find("note", attrs= {"type": "translation"})
            translation = hi_rend(translation)
            f_latex.write(str(translation.text) + "\n\n")


if __name__ == '__main__':
    dir_name_in = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/XML"
    dir_name_out = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/LaTeX"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("sz.xml"):
                continue
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))
    begin = time.time()
    for i in filelist_in:
        out = i.replace(dir_name_in, dir_name_out).replace(".xml", ".tex")
        make_latex(i, out)
    end = time.time()
    print(end - begin)
