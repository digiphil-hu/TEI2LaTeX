# This script converts letters encoded in XML to LaTeX files.
# Author: gaborpalko
# TODO TEI XML pre-processing: <?oxy...> comment removal
# TODO TEI XML pre-processing: _1 filename change to -1: "([^\.]15\d\d\d\d\d\d)(_)(\d)" => \1-\3

import time
import os
from bs4 import BeautifulSoup
import re


def normalize_text(string):
    # Input and output: STRING!!!!
    string = re.sub("[\n\t\s]+", " ", string)
    return string


def hi_rend(soup):
    # Input and output: soup object
    soup = normalize_text(str(soup))
    soup = re.sub('\s+', " ", soup)
    soup = re.sub('<hi +rend *= *"italic" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textit{\\1}\\2', soup)
    soup = re.sub('<hi +rend *= *"smallcap" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textsc{\\1}\\2', soup)
    soup = re.sub('<hi +rend *= *"bold" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textbf{\\1}\\2', soup)
    soup = BeautifulSoup(soup, "xml")
    return(soup)


def header2latex(soup):
    header_str = ""

    # Insert LaTeX doc header
    with open("begin.txt", "r", encoding="utf8") as f_begin:
        begin = f_begin.read()
        header_str += begin

    header_str += "\n" + "\\begin{center}" + "\n"

    # Insert title
    title = str(soup.fileDesc.titleStmt.title.text)
    title = normalize_text(title)
    header_str += "\n" + "\\section{" + title + "}" + "\n\n"

    # Insert manuscript description
    country = str(soup.country.text)
    settlement = str(soup.settlement.text)
    institution = str(soup.institution.text)
    repository = str(soup.repository.text)
    header_str += "\\textit{Manuscript used}: " + country + ", " + settlement + ", "\
                 + institution + ", " + repository + "\n\n"

    # Insert critIntro (Notes, Photo copy). Runs only on each <p> in critIntro
    critIntro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for i in critIntro:
        for p in i.find_all("p"):
            p = hi_rend(p).text
            header_str += p + "\n\n"

    # Insert publication
    for publication in soup.notesStmt.find_all("note", attrs={"type": "publication"}):
        publication = hi_rend(publication)
        header_str += str(publication.text) + "\n"

    # Insert translation
    for translation in soup.notesStmt.find("note", attrs={"type": "translation"}):
        translation = hi_rend(translation)
        header_str += str(translation.text) + "\n"

    header_str += "\n" + "\end{center}" + "\n"

    return header_str


def text2latex(soup):
    text_latex = ""

    # Regesta: insert into latex string and then remove from soup object
    for p in soup.floatingText.find_all("p"):
        p = hi_rend(p).text
    text_latex += "\n" + "\\begin{quote}" + "\n" + p + "\n" + "\end{quote}" + "\n"
    soup.floatingText.extract()

    # Letter text
    text_latex += "\n" + "\\selectlanguage{latin}" + "\n" + "\\beginnumbering" + "\n" + "\\firstlinenum{5}" + "\n" + \
                  "\linenumincrement{5}" + "\n"

    for p in soup.body.div.find_all("p"):
        p = hi_rend(p).text
        text_latex += "\n" + "\psart" + "\n" + p + "\n" + "\pend" + "\n"

        # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = normalize_text(div.head.text)
        text_latex += "\n" + "\psart" + "\n" + "\\textit{" + verso_head + "}" + "\n" + "\pend" + "\n"
        for p in div.find_all("p"):
            p = hi_rend(p)
            text_latex += "\n" + "\psart" + "\n" + p.text + "\n" + "\pend" + "\n"

    text_latex += "\n" + "\endnumbering" + "\n" + "\\selectlanguage{english}" + "\n"

    return text_latex


def main(xml, latex):
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")

        # Delete <ref> tags
        for i in sp.find_all("ref"):
            i.extract()

        with open(latex, "w", encoding="utf8") as f_latex:

            # Transform header
            h = header2latex(sp.teiHeader)
            f_latex.write(h)

            # Transform text
            t = text2latex(sp.find("text"))
            f_latex.write(t)


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
        main(i, out)
    end = time.time()
    print(end - begin)
