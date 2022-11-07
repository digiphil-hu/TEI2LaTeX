# This script converts letters encoded in XML to LaTeX files.
# Author: https://github.com/gaborpalko
# TODO TEI XML pre-processing: <?oxy...> comment removal
# https://docs.google.com/document/d/1Jpkln-_kjH_ONQYcJlGn9BBv1clW4ANm/edit
# https://docs.google.com/document/d/1EMKpwDzhvV7jF08vTfOqr2wIKCMFoJTaOfnaCcibajo/edit
# TODO Empty paragraph: \pstart \pend

import time
import os
from bs4 import BeautifulSoup
import re
from normalize import normalize_text
from paragraph import paragraph


def note_critic(note):

    para_str = str(note)
    for note_cr_tag in note.find_all("note", attrs={"type": "critic"}):
        note_text = note_cr_tag.text
        note_cr_str = str(note_cr_tag)
        note_cr_latex = "\\footnoteA{" + note_text + "}"
        para_str = para_str.replace(note_cr_str, note_cr_latex)
    note = BeautifulSoup(para_str, "xml")
    return note


def quote(quot, note):
    # <quote><note type="quote">
    # Milestone p missing!
    # Are they really "words"?
    if note is None:
        note = BeautifulSoup("<note\>", "xml")
    q_text = quot.text
    q_text = q_text.replace("{[}BEKEZDÉSHATÁR{]}", "").replace("OLDALTÖRÉS", "")
#   print(q_text)
    q_text = re.sub("\\\edtext.+}}", "", q_text).replace("  ", " ").rstrip("., ").lstrip(" ")
    q_text = re.sub("\\\index\[\w+\]{\w+}", "", q_text)
#   print(q_text)
    q_list = q_text.split(" ")
    if len(q_list) > 2:
        firstword = q_list[0].rstrip(".,")
        lastword = q_list[-1].rstrip(".,")
        #        print("Quote első és utsó szavai: ", firstword, "------", lastword)
        q_keyword = firstword + "\ldots{} " + lastword
    if len(q_list) <= 2:
        q_keyword = q_text.rstrip(".,")
    #        print("Rövid quote: ", q_keyword)
    n_new = "\edtext{" + q_text + "}{\lemma{" + q_keyword + "}\Afootnote{" + note.text + "}}"
    quot.string = n_new
    quot.unwrap()
    note.extract()


def header2latex(soup):
    header_str = ""

    #    Insert LaTeX doc header
    #    with open("begin.txt", "r", encoding="utf8") as f_begin:
    #        begin = f_begin.read()
    #        header_str += begin

    header_str += "\n" + "\\begin{center}" + "\n"

    # Insert title
    title1 = soup.fileDesc.titleStmt.find("title", attrs={"type": "num"})
    title1 = normalize_text(title1, {"all"}).text
    title2 = soup.fileDesc.titleStmt.find("title", attrs={"type": "main"})
    title2 = normalize_text(title2, {"all"}).text
    header_str += "\n" + "\\section{" + title1 + " - " + title2 + "}" + "\n\n"

    # Insert manuscript description
    #    country = soup.country.text
    #    settlement = soup.settlement.text
    institution = soup.institution.text
    repository = soup.repository.text
    folio = soup.measure.text
    header_str += "\\textit{Manuscript used}: " + institution + ", " + repository + ", fol. " + folio + "\n\n"

    # Insert critIntro (Photo copy). Runs only on each <p> in critIntro
    crit_intro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for elem in crit_intro:
        for p in elem.find_all("p"):
            if p.text.startswith("Photo copy:") and p.text != "Photo copy:":
                p = normalize_text(p, {"all"}).text
                header_str += p + "\n\n"

    # Insert publication
    for publication in soup.notesStmt.find_all("note", attrs={"type": "publication"}):
        if publication.text == "" or publication.text == " ":
            continue
        else:
            publication = normalize_text(publication, {"all"})
            header_str += "\\textsc{" + "Published: " + "}" + publication.text + "\n"

    # Insert translation
    for translation in soup.notesStmt.find_all("note", attrs={"type": "translation"}):
        if translation.text == "" or translation.text == " ":
            continue
        else:
            translation = normalize_text(translation, {"all"})
            header_str += translation.text + "\n"

    # Insert critIntro (Notes:). Runs only on each <p> in critIntro
    crit_intro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for elem in crit_intro:
        for p in elem.find_all("p"):
            if p.text.startswith("Notes:") and p.text != "Notes:":
                p = normalize_text(p, {"all"}).text
                header_str += p + "\n\n"

    header_str += "\n" + r"\end{center}" + "\n"
    return header_str


def text2latex(soup):
    text_latex = ""

    # Regesta: insert <floatingText> into latex string and then remove tag from soup object
    for p in soup.floatingText.find_all("p"):
        p = normalize_text(p, {"all"}).text
        #    text_latex += "\n" + "\\begin{quote}" + "\n" + p + "\n" + "\end{quote}" + "\n"
        text_latex += "\n" + "\medskip{}" + "\n" + "\\noindent{}{\small\\textit{" + p + "}}"
    soup.floatingText.extract()

    # Letter text
    text_latex += "\n" + "\\selectlanguage{latin}" + "\n" + "\\beginnumbering" + "\n" + "\\firstlinenum{5}" + "\n" + \
                  "\linenumincrement{5}" + "\n"

    for p in soup.body.div.find_all("p"):
        p = paragraph(p)
        for q in p.find_all("quote"):
            n = q.next_sibling
            quote(q, n)
        text_latex += "\n" + "\pstart" + "\n" + p.text + "\n" + "\pend" + "\n"

        # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = normalize_text(div.head, {"all"})
        text_latex += "\n" + "\pstart" + "\n" + "\\textit{" + verso_head.text + "}" + "\n" + "\pend" + "\n"
        for p in div.find_all("p"):
            p = paragraph(p)
            for q in p.find_all("quote"):
                n = q.next_sibling
                quote(q, n)
            text_latex += "\n" + "\pstart" + "\n" + p.text + "\n" + "\pend" + "\n"

    text_latex += "\n" + "\endnumbering" + "\n" + "\\selectlanguage{english}" + "\n"
    text_latex += "\n" + "\pagebreak" + "\n"

    return text_latex


def main(xml, latex):
    print(xml.lstrip("/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/XML"))
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")

        # Delete <ref> tags
        for elem in sp.find_all("ref"):
            elem.extract()

        with open("latex2.tex", "a", encoding="utf8") as f_latex:
            # Write header
            h = header2latex(sp.teiHeader)
            f_latex.write(h)

            # Write text
            t = text2latex(sp.find("text"))
            f_latex.write(t)


if __name__ == '__main__':
    with open("latex2.tex", "w", encoding="utf8") as f_w:
        with open("begin.txt", "r", encoding="utf8") as f_r:
            start = f_r.read()
            f_w.write(start)
    dir_name_in = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/XML2"
    dir_name_out = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/LaTeX"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("sz.xml"):
                filelist_in.append(os.path.join(dirpath, x))
                continue
            elif x.endswith(".xml"):
                filelist_in.append(os.path.join(dirpath, x))
    filelist_in.sort()
    begin = time.time()
    for i in filelist_in:
        out = i.replace(dir_name_in, dir_name_out).replace(".xml", ".tex")
        main(i, out)
    with open("latex2.tex", "a", encoding="utf8") as f_w:
        # End
        f_w.write("\n" + "\\end{document}")
    end = time.time()
    print(end - begin)
