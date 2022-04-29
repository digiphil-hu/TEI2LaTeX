# This script converts letters encoded in XML to LaTeX files.
# Author: gaborpalko
# TODO Everythhing!

import time
import os
from bs4 import BeautifulSoup


def make_latex(xml, latex):
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")
        with open(latex, "w", encoding="utf8") as f_latex:

            # Insert LaTeX doc header
            with open("begin.txt", "r", encoding="utf8") as f_begin:
                begin = f_begin.read()
                f_latex.write(begin)

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
            critIntro = sp.notesStmt.find("note", attrs= {"type": "critIntro"})
            critIntro_notes = str(critIntro.p.text).lstrip("Notes:")
            critIntro_photo = str(critIntro.p.find_next_sibling().text).lstrip("Photo copy:")
            f_latex.write("\\textbf{Notes}: " + critIntro_notes + "\n\n" + "\\textbf{Photo copy}: " + critIntro_photo
                          + "\n\n")


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
