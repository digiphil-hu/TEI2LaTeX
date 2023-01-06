# This script converts letters encoded in XML to LaTeX files.
# Author: https://github.com/gaborpalko
# TODO TEI XML pre-processing: <?oxy...> comment removal


import time
import os
from bs4 import BeautifulSoup
import re
from normalize import normalize_text, latex_escape
from paragraph import paragraph
from header import header2latex


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
        q_keyword = firstword + r"\ldots{} " + lastword
    if len(q_list) <= 2:
        q_keyword = q_text.rstrip(".,")
    #        print("Rövid quote: ", q_keyword)
    n_new = r"\edtext{" + q_text + r"}{\lemma{" + q_keyword + r"}\Afootnote{" + note.text + "}}"
    quot.string = n_new
    quot.unwrap()
    note.extract()


def text2latex(soup, num):
    text_latex = ""

    # Regesta: insert <floatingText> into latex string and then remove tag from soup object
    for float_p in soup.floatingText.find_all("p"):
        float_p = normalize_text(float_p, {"all"}).text
        text_latex += r"\noindent{}\textit{\small " + float_p + "}"
    soup.floatingText.extract()

    text_latex += "\n\n" + r"\medskip{}" + "\n"

    # Letter text
    text_latex += "\n" \
                  + r"\selectlanguage{latin}" + "\n" \
                  + r"\makeatletter" + "\n" \
                  + r"\renewcommand*{\footfootmarkA}{" + num + r"\,\textsuperscript{\@nameuse{@thefnmarkA}\,}}" \
                  + r"\makeatother" + "\n" \
                  + r"\beginnumbering" + "\n" \
                  + r"\firstlinenum{5}" + "\n" \
                  + r"\linenumincrement{5}" + "\n" \
                  + r"\Xtxtbeforenumber[A]{" + num + ",}" + "\n"

    # Paragraph
    for p in soup.body.div.find_all("p"):
        p = paragraph(p)
        for q in p.find_all("quote"):
            n = q.next_sibling
            quote(q, n)
        text_latex += "\n" \
                      + r"\pstart" + "\n" \
                      + p.text + "\n" \
                      + r"\pend" + "\n"

        # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = normalize_text(div.head, {"all"})
        text_latex += "\n" \
                      + r"\pstart" + "\n" \
                      + r"\textit{" + verso_head.text + "}" + "\n" \
                      + r"\pend" + "\n"

        for p in div.find_all("p"):
            p = paragraph(p)
            for q in p.find_all("quote"):
                n = q.next_sibling
                quote(q, n)
            text_latex += "\n" \
                          + r"\pstart" + "\n" \
                          + p.text + "\n" \
                          + r"\pend" + "\n"

    text_latex += "\n" \
                  + r"\endnumbering" + "\n\n" \
                  + r"\selectlanguage{english}" + "\n"
    text_latex += "\n" + r"\pagebreak" + "\n\n"

    text_latex = latex_escape(text_latex)

    return text_latex


def main(xml, latex):
    print(xml.lstrip("/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/XML"))
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")

        # Delete <ref> tags
        # for elem in sp.find_all("ref"):
        #    elem.extract()

        with open("latex2.tex", "a", encoding="utf8") as f_latex:
            # Write header
            h = header2latex(sp.teiHeader)
            f_latex.write(h[0])
            title_num = h[1]

            # Write text
            t = text2latex(sp.find("text"), title_num)
            f_latex.write(t)


if __name__ == '__main__':
    with open("latex2.tex", "w", encoding="utf8") as f_w:
        with open("begin.txt", "r", encoding="utf8") as f_r:
            start = f_r.read()
            f_w.write(start)
    dir_name_in = "/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/XML2"
    dir_name_out = "Olahus/LaTeX"
    filelist_in = []
    for dirpath, subdirs, files in os.walk(dir_name_in):
        for x in files:
            if x.endswith("sz.xml"):
                # filelist_in.append(os.path.join(dirpath, x))
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
        f_w.write(r"\end{document}")
    end = time.time()
    print(end - begin)