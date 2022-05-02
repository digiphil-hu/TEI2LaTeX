# This script converts letters encoded in XML to LaTeX files.
# Author: gaborpalko
# TODO TEI XML pre-processing: <?oxy...> comment removal
# TODO TEI XML pre-processing: _1 filename change to -1: "([^\.]15\d\d\d\d\d\d)(_)(\d)" => \1-\3

import time
import os
from bs4 import BeautifulSoup
import re


def previous_word(tag):
    prev_list = tag.previous_element.text.split(" ")
    if len(prev_list) > 2:
        prev_w = prev_list[-2]
    else:
        prev_w = "Unkonwn"
    return prev_w


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


def note_critic(para):
    # Input: normalized soup object preprocessed by the function: hi_rend()
    para_str = str(para)
    for note_cr_tag in para.find_all("note", attrs={"type": "critic"}):
        note_text = note_cr_tag.text
        note_cr_str = str(note_cr_tag)
        note_cr_latex = "\\footnoteA{" + note_text + "}"
        para_str = para_str.replace(note_cr_str, note_cr_latex)
    para = BeautifulSoup(para_str, "xml")
    return para


def del_add(para):
    # Input: <p> after hi_rend() including normalization.
    # TODO: <add>
    for d in para.find_all("del"):
        # <del><add>
        if str(d.next_sibling).startswith("<add"):
            d_cor = d["corresp"]
            d_text = d.text
            a_cor = d.next_sibling["corresp"]
            a_text = d.next_sibling.text
            if d_cor == a_cor:
                d_new = "\edtext{"+ a_text +"}{\lemma{" + a_text + "}\Afootnote{\\textit{" + a_cor + " corr. ex} " + d_text + "}}"
            else:
                lemma = previous_word(d)
                d_new = "\edtext{" + "}{\lemma{" + lemma + "}\Afootnote{\\textit{" + d_cor + " del. ex }" \
                        + lemma + " " + d_text + "}}\edtext{" + a_text + "}{\lemma{" + a_text + "}\Afootnote{\\textit{" \
                        + a_cor + " add.}}}"
            print(d_new)
            d.next_sibling.extract()
            d.string = d_new
            d.unwrap()
        else:
            d_cor = d["corresp"]
            d_text = d.text
            lemma = previous_word(d)
            d_new = "\edtext{" + "}{\lemma{" + lemma + "}\Afootnote{\\textit{" + d_cor + " del. ex }" \
                        + lemma + " " + d_text + "}}"
            print(d_new)
            d.string = d_new
            d.unwrap()
    return para


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
    for translation in soup.notesStmt.find_all("note", attrs={"type": "translation"}):
        translation = hi_rend(translation)
        header_str += str(translation.text) + "\n"

    header_str += "\n" + "\end{center}" + "\n"
    return header_str


def text2latex(soup):
    text_latex = ""

    # Regesta: insert <floatingText> into latex string and then remove tag from soup object
    for p in soup.floatingText.find_all("p"):
        p = hi_rend(p).text
    text_latex += "\n" + "\\begin{quote}" + "\n" + p + "\n" + "\end{quote}" + "\n"
    soup.floatingText.extract()

    # Letter text
    text_latex += "\n" + "\\selectlanguage{latin}" + "\n" + "\\beginnumbering" + "\n" + "\\firstlinenum{5}" + "\n" + \
                  "\linenumincrement{5}" + "\n"

    for p in soup.body.div.find_all("p"):
        p = hi_rend(p)
        p = note_critic(p)
        p = del_add(p)
        text_latex += "\n" + "\pstart" + "\n" + p.text + "\n" + "\pend" + "\n"

        # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = normalize_text(div.head.text)
        text_latex += "\n" + "\pstart" + "\n" + "\\textit{" + verso_head + "}" + "\n" + "\pend" + "\n"
        for p in div.find_all("p"):
            p = hi_rend(p)
            p = note_critic(p)
            p = del_add(p)
            text_latex += "\n" + "\pstart" + "\n" + p.text + "\n" + "\pend" + "\n"

    text_latex += "\n" + "\endnumbering" + "\n" + "\\selectlanguage{english}" + "\n"
    text_latex += "\n" + "\pagebreak" + "\n"
    text_latex += "\n" + "\end{document}" + "\n"
    return text_latex


def main(xml, latex):
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")

        # Delete <ref> tags, <placeName>, <persName>
        for i in sp.find_all("ref"):
            i.extract()
        for i in sp.find_all("placeName"):
            i.extract()
        for i in sp.find_all("persName"):
            i.extract()

        with open(latex, "w", encoding="utf8") as f_latex:

            # Write header
            h = header2latex(sp.teiHeader)
            f_latex.write(h)

            # Write text
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
