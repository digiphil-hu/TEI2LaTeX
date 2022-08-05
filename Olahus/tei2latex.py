# This script converts letters encoded in XML to LaTeX files.
# Author: gaborpalko
# TODO TEI XML pre-processing: <?oxy...> comment removal
# https://docs.google.com/document/d/1Jpkln-_kjH_ONQYcJlGn9BBv1clW4ANm/edit
# https://docs.google.com/document/d/1EMKpwDzhvV7jF08vTfOqr2wIKCMFoJTaOfnaCcibajo/edit
# TODO Empty \edtext{} ???
# TODO Empty paragraph: \pstart \pend

import time
import os
from bs4 import BeautifulSoup
import re


def previous_word(tag):
    if tag.previous_element.string is not None and tag.previous_element.text != " ":
        print("FIRST", tag, tag.previous_element.text)
    elif tag.previous_element.previous_element is not None and tag.previous_element.previous_element.text != " ":
        print("SECOND", tag, tag.previous_element.previous_element.text)
    else:
        print("THIRD", tag)
    return "UNKNOWN"


def normalize_text(string):
    # Input and output: STRING!!!! [ and ] => {}
    string = re.sub("[\n\t\s]+", " ", string)
    string = re.sub('\s+', " ", string)
    string = re.sub("\[", "{[}", string)
    string = re.sub("\]", "{]}", string)
    string = re.sub("_", "\\_", string)
    string = re.sub("#", "\\#", string)
    string = re.sub("<milestone unit=\"p\"/>", "{[}BEKEZDÉSHATÁR{]}", string)
    string = re.sub("corresp=\"Olahus\"", "corresp=\"O.\"", string)
    string = re.sub("corresp=\"editor\"", "corresp=\" \"", string)  # <del corresp="editor">
    return string


def hi_rend(soup):
    # Input and output: soup object
    soup = normalize_text(str(soup))
    soup = BeautifulSoup(soup, "xml")

    # Names
    for name in soup.find_all("persName"):
        name.string = "\index[pers]{" + name.text + "}" + name.text
        name.unwrap()
    for place in soup.find_all("placeName"):
        place.string = "\index[pers]{" + place.text + "}" + place.text
        place.unwrap()

    # hi rend. As italic and small-cap may be under bold, two cycles are needed.
    # Bold under small-cap or italic is not supported!
    for hi in soup.find_all("hi"):
        if len(hi.find_all("hi")) == 0:
            hi_text = hi.text
            if hi["rend"] == "italic":
                hi.string = "\\textit{" + hi_text + "}"
                hi.unwrap()
            if hi["rend"] == "smallcap":
                hi.string = "\\textsc{" + hi_text + "}"
                hi.unwrap()
    for hi in soup.find_all("hi"):
        hi_text = hi.text
        if len(hi.find_all("hi")) == 0:
            if hi["rend"] == "bold":
                hi.string = "\\textbf{" + hi_text + "}"
                hi.unwrap()
        else:
            print(hi)

    """
    soup = re.sub('<hi +rend *= *"italic" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textit{\\1}\\2', soup)
    soup = re.sub('<hi +rend *= *"smallcap" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textsc{\\1}\\2', soup)
    soup = re.sub('<hi +rend *= *"bold" *>(.*?)(:?)(?:</hi>)',
                  '\\\\textbf{\\1}\\2', soup)
    """
    return soup


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


def quote(quot, note):
    # <quote><note type="quote">
    # Milestone p missing!
    if note is None:
        note = BeautifulSoup("<note\>", "xml")
    q_text = quot.text
    q_list = q_text.split(" ")
    if len(q_list) > 2:
        firstword = q_list[0]
        lastword = q_list[-1]
        q_keyword = firstword + "\ldots{} " + lastword
    if len(q_list) <= 2:
        q_keyword = quot.text
    n_new = "\edtext{" + q_text + "}{\lemma{" + q_keyword + "}\Afootnote{" + note.text + "}}"
    quot.string = n_new
    quot.unwrap()
    note.extract()


def paragraph(para):
    # Input: <p> after hi_rend() including normalization.

    # <del> not followed by <add>
    # TODO <note> or <add> under <del>?
    for d in para.find_all("del"):
        if not str(d.next_sibling).startswith("<add"):
            d_cor = d["corresp"]
            d_text = d.text
            lemma = previous_word(d)
            d_new = "\edtext{" + lemma + "}{\Afootnote{\\textit{" + d_cor + " del. ex }" + lemma + " " + d_text + "}}"
            d.string = d_new
            d.unwrap()

    # <del><add>
    for d in para.find_all("del"):
        if str(d.next_sibling).startswith("<add"):
            d_cor = d["corresp"]
            d_text = d.text
            a_cor = d.next_sibling["corresp"]
            a_text = d.next_sibling.text
            if d_cor == a_cor:
                d_new = "\edtext{" + a_text + "}{\Afootnote{\\textit{" + a_cor + " corr. ex} " + d_text + "}}"
            else:
                continue
            d.next_sibling.extract()
            d.string = d_new
            d.unwrap()

    # <add type=insert>
    for a in para.find_all("add", attrs={"type": "insert"}):
        if len(a.find_all("add")) == 0:
            a_text = a.text
            a_cor = a["corresp"]
            a_new = "\edtext{" + a_text + "}{\Afootnote{\\textit{" + a_cor + " add.}}}"
            a.string = a_new
            a.unwrap()

    # If <add type=insert> has <add> as child:
    for a in para.find_all("add", attrs={"type": "insert"}):
        if len(a.find_all("add")) == 0:
            a_text = a.text
            a_cor = a["corresp"]
            a_new = "\edtext{" + a_text + "}{\Afootnote{\\textit{" + a_cor + " add.}}}"
            a.string = a_new
            a.unwrap()

    # <choice> <supplied>
    for ch in para.find_all("choice"):
        if ch.supplied.corr is not None and ch.supplied.corr.string is not None:
            cor_cor = ch.supplied.corr.text
            ch.supplied.corr.extract()
            cor_sup = ch.supplied.text
            ch.string = cor_sup + "<" + cor_cor + ">"
            ch.unwrap()
        elif ch.supplied.corr is not None and ch.supplied.corr.string is None:
            ch.string = "<\ldots{}> "
            ch.unwrap()
        else:
            orig_text = ch.orig.text
            sup_text = ch.supplied.text
            ch_new = "\edtext{" + sup_text + "}{\Afootnote{\\textit{corr. ex} " + orig_text + "}}"
            ch.supplied.extract()
            ch.string = ch_new
            ch.unwrap()
    return para


def header2latex(soup):
    header_str = ""

    #    Insert LaTeX doc header
    #    with open("begin.txt", "r", encoding="utf8") as f_begin:
    #        begin = f_begin.read()
    #        header_str += begin

    header_str += "\n" + "\\begin{center}" + "\n"

    # Insert title
    title = str(soup.fileDesc.titleStmt.title.text)
    title = normalize_text(title)
    header_str += "\n" + "\\section{" + title + "}" + "\n\n"

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
                p = hi_rend(p).text
                header_str += p + "\n\n"

    # Insert publication
    for publication in soup.notesStmt.find_all("note", attrs={"type": "publication"}):
        if publication.text == "" or publication.text == " ":
            continue
        else:
            publication = hi_rend(publication)
            header_str += "\\textsc{" + "Published: " + "}" + str(publication.text) + "\n"

    # Insert translation
    for translation in soup.notesStmt.find_all("note", attrs={"type": "translation"}):
        if translation.text == "" or translation.text == " ":
            continue
        else:
            translation = hi_rend(translation)
            header_str += str(translation.text) + "\n"

    # Insert critIntro (Notes:). Runs only on each <p> in critIntro
    crit_intro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for elem in crit_intro:
        for p in elem.find_all("p"):
            if p.text.startswith("Notes:") and p.text != "Notes:":
                p = hi_rend(p).text
                header_str += p + "\n\n"

    header_str += "\n" + "\end{center}" + "\n"
    return header_str


def text2latex(soup):
    text_latex = ""

    # Regesta: insert <floatingText> into latex string and then remove tag from soup object
    for p in soup.floatingText.find_all("p"):
        p = hi_rend(p).text
        #    text_latex += "\n" + "\\begin{quote}" + "\n" + p + "\n" + "\end{quote}" + "\n"
        text_latex += "\n" + "\medskip{}" + "\n" + "\\noindent{}{\small\\textit{" + p + "}}"
    soup.floatingText.extract()

    # Letter text
    text_latex += "\n" + "\\selectlanguage{latin}" + "\n" + "\\beginnumbering" + "\n" + "\\firstlinenum{5}" + "\n" + \
                  "\linenumincrement{5}" + "\n"

    for p in soup.body.div.find_all("p"):
        p = hi_rend(p)
        p = note_critic(p)
        p = paragraph(p)
        for q in p.find_all("quote"):
            n = q.next_sibling
            quote(q, n)
        text_latex += "\n" + "\pstart" + "\n" + p.text + "\n" + "\pend" + "\n"

        # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = hi_rend(div.head)
        text_latex += "\n" + "\pstart" + "\n" + "\\textit{" + verso_head.text + "}" + "\n" + "\pend" + "\n"
        for p in div.find_all("p"):
            p = hi_rend(p)
            p = note_critic(p)
            p = paragraph(p)
            for q in p.find_all("quote"):
                n = q.next_sibling
                quote(q, n)
            text_latex += "\n" + "\pstart" + "\n" + p.text + "\n" + "\pend" + "\n"

    text_latex += "\n" + "\endnumbering" + "\n" + "\\selectlanguage{english}" + "\n"
    text_latex += "\n" + "\pagebreak" + "\n"
    #    text_latex += "\n" + "\end{document}" + "\n"
    return text_latex


def main(xml, latex):
    # print(xml)
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
    dir_name_in = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/XML"
    dir_name_out = "/home/elte-dh-celestra/PycharmProjects/TEI2LaTeX/Olahus/LaTeX"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("sz.xml"):
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
