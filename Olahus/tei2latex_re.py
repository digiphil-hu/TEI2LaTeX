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
import normalize as nr


def last_word(txt):
    txt = re.sub(".text[si][ct]{([^}]+)}", "\\0", txt)
    txt = re.sub(".footnoteA{[^}]+}", " ", txt)
    txt = re.sub("{\[}\d+\.{\]}", "", txt)
    txt_list = txt.rstrip(",. );!?:").split(" ")
    txt = txt_list[-1]
    if txt.startswith("\index[pers]"):
        txt_list = txt.split("}")
        txt = txt_list[-1]
    txt = txt.lstrip("(")
    return txt


def previous_word(tag):
    # <del> anywhere, text element precedes it
    # todo [2.]
    if tag.previous_element.name is None and len(tag.previous_element.text.rstrip(".,!?; ")) > 0:
        raw_text = tag.previous_element.text
        lastword = last_word(raw_text)
        if lastword != "":
            return lastword

    if tag.find_parent().name == "add":
        raw_text = tag.find_parent().text
        lastword = last_word(raw_text)
        if lastword != "":
            return lastword

    #    print(f"Parent: {tag.find_parent().name}  Prev: {tag.previous_element.name} Deleted text: {tag.text}")
    return "Unknown"


def note_critic(note):

    note = nr.normalize_text(note, {"all"})
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


def paragraph(para):
    # Input: <p> without normalization.
    para = nr.normalize_text(para, {"all"})

    for appTag in para.find_all("app"):
        if appTag.lem.find_next("del") is not None:
            #  print("lem alatt del:", appTag.lem)
            continue
        elif appTag.rdg.find_next("del") is not None:
            #  print("rdg alatt del:", appTag.rdg)
            continue
        else:
            lem_text = appTag.lem.text
            rdg_text = appTag.rdg.text
            lem_wit = appTag.lem["wit"].split("#")[-1]
            rdg_wit = appTag.rdg["wit"].split("#")[-1]
            appTag.string = "\edtext{" + lem_text + "}{\Afootnote{corr. sec. " + rdg_wit + " ex " + lem_wit + \
                            " " + rdg_text + "}}"
            print(appTag.string)
            appTag.unwrap()

    for delAlone in para.find_all("del"):
        if not str(delAlone.next_sibling).startswith("<add"):
            delAlone = del_tag(delAlone)
            delAlone.unwrap()

    # <del><add>
    for delAddTag in para.find_all("del"):
        if str(delAddTag.next_sibling).startswith("<add"):
            delAddTag = del_add(delAddTag)
            delAddTag.next_sibling.extract()
            delAddTag.unwrap()

    # <add type=insert>
    for addInsert in para.find_all("add", attrs={"type": "insert"}):
        if len(addInsert.find_all("add")) == 0:
            addInsert = add_insert(addInsert)
            addInsert.unwrap()
        else:
            addInsertChild = addInsert.add
            addInsertChild = add_insert(addInsertChild)
            addInsertChild.unwrap()
            add_insert(addInsert)
            addInsert.unwrap()

    # <choice> <supplied>
    for ch in para.find_all("choice"):
        ch = choice_supplied(ch)
        ch.unwrap()

    return para


def del_tag(del_tag):
    # <del> not followed by <add>
    # TODO <note> or <add> under <del>?
    d_cor = del_tag["corresp"]
    d_text = del_tag.text
    lemma = previous_word(del_tag)
    d_new = "\edtext{" + "}{\lemma{" + lemma + "}\Afootnote{\\textit{" + d_cor + " del. ex }" \
            + lemma + " " + d_text + "}}"
    del_tag.string = d_new
    return del_tag

def del_add(del_tag):
    d_cor = del_tag["corresp"]
    d_text = del_tag.text
    a_cor = del_tag.next_sibling["corresp"]
    a_text = del_tag.next_sibling.text
    if d_cor == a_cor:
        d_new = "\edtext{" + a_text + "}{\Afootnote{\\textit{" + a_cor + " corr. ex} " + d_text + "}}"
    del_tag.string = d_new
    return del_tag


def add_insert(add_tag):
    a_text = add_tag.text
    a_cor = add_tag["corresp"]
    a_new = "\edtext{" + a_text + "}{\Afootnote{\\textit{" + a_cor + " add.}}}"
    add_tag.string = a_new
    return add_tag


def choice_supplied(choice):
    if choice.supplied.corr is not None and choice.supplied.corr.string is not None:
        cor_cor = choice.supplied.corr.text
        choice.supplied.corr.extract()
        cor_sup = choice.supplied.text
        choice.string = cor_sup + "<" + cor_cor + ">"
    elif choice.supplied.corr is not None and choice.supplied.corr.string is None:
        choice.string = "<\ldots{}> "
    else:
        orig_text = choice.orig.text
        sup_text = choice.supplied.text
        ch_new = "\edtext{" + sup_text + "}{\Afootnote{\\textit{corr. ex} " + orig_text + "}}"
        choice.supplied.extract()
        choice.string = ch_new
    return choice


def header2latex(soup):
    header_str = ""

    #    Insert LaTeX doc header
    #    with open("begin.txt", "r", encoding="utf8") as f_begin:
    #        begin = f_begin.read()
    #        header_str += begin

    header_str += "\n" + "\\begin{center}" + "\n"

    # Insert title
    title1 = soup.fileDesc.titleStmt.find("title", attrs={"type": "num"})
    title1 = nr.normalize_text(title1, {"all"}).text
    title2 = soup.fileDesc.titleStmt.find("title", attrs={"type": "main"})
    title2 = nr.normalize_text(title2, {"all"}).text
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
                p = nr.normalize_text(p, {"all"}).text
                header_str += p + "\n\n"

    # Insert publication
    for publication in soup.notesStmt.find_all("note", attrs={"type": "publication"}):
        if publication.text == "" or publication.text == " ":
            continue
        else:
            publication = nr.normalize_text(publication, {"all"})
            header_str += "\\textsc{" + "Published: " + "}" + publication.text + "\n"

    # Insert translation
    for translation in soup.notesStmt.find_all("note", attrs={"type": "translation"}):
        if translation.text == "" or translation.text == " ":
            continue
        else:
            translation = nr.normalize_text(translation, {"all"})
            header_str += translation.text + "\n"

    # Insert critIntro (Notes:). Runs only on each <p> in critIntro
    crit_intro = soup.notesStmt.find_all("note", attrs={"type": "critIntro"})
    for elem in crit_intro:
        for p in elem.find_all("p"):
            if p.text.startswith("Notes:") and p.text != "Notes:":
                p = nr.normalize_text(p, {"all"}).text
                header_str += p + "\n\n"

    header_str += "\n" + "\end{center}" + "\n"
    return header_str


def text2latex(soup):
    text_latex = ""

    # Regesta: insert <floatingText> into latex string and then remove tag from soup object
    for p in soup.floatingText.find_all("p"):
        p = nr.normalize_text(p, {"all"}).text
        #    text_latex += "\n" + "\\begin{quote}" + "\n" + p + "\n" + "\end{quote}" + "\n"
        text_latex += "\n" + "\medskip{}" + "\n" + "\\noindent{}{\small\\textit{" + p + "}}"
    soup.floatingText.extract()

    # Letter text
    text_latex += "\n" + "\\selectlanguage{latin}" + "\n" + "\\beginnumbering" + "\n" + "\\firstlinenum{5}" + "\n" + \
                  "\linenumincrement{5}" + "\n"

    for p in soup.body.div.find_all("p"):
        p = note_critic(p) #  Change needed: method input must be <note> and not <p>
        p = paragraph(p)
        for q in p.find_all("quote"):
            n = q.next_sibling
            quote(q, n)
        text_latex += "\n" + "\pstart" + "\n" + p.text + "\n" + "\pend" + "\n"

        # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = nr.normalize_text(div.head, {"all"})
        text_latex += "\n" + "\pstart" + "\n" + "\\textit{" + verso_head.text + "}" + "\n" + "\pend" + "\n"
        for p in div.find_all("p"):
            p = note_critic(p) # Change needed: method input must be <note> and not <p> ??????
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
