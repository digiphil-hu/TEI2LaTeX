# This script converts letters encoded in XML to LaTeX files.
# Author: https://github.com/gaborpalko
# TODO TEI XML pre-processing: <?oxy...> comment removal


import time
from bs4 import BeautifulSoup

from Olahus.count import count_xml_body, count_latex_body, file_list, change_xml_filename
from normalize import normalize_text, latex_escape
from paragraph import paragraph
from header import header2latex


def text2latex(soup, letternum, filename):
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
                  + r"\renewcommand*{\footfootmarkA}{" + letternum + r"\,\textsuperscript{\@nameuse{@thefnmarkA}\,}}" \
                  + r"\makeatother" + "\n" \
                  + r"\beginnumbering" + "\n" \
                  + r"\firstlinenum{5}" + "\n" \
                  + r"\linenumincrement{5}" + "\n" \
                  + r"\Xtxtbeforenumber[A]{" + letternum + ",}" + "\n" \
                  + r"\Xtxtbeforenumber[B]{" + letternum + ",}" + "\n"

    # Paragraph
    for p in soup.body.div.find_all("p"):
        p = paragraph(p, filename=filename)
        if len(p.text.replace(" ", "")) > 0:
            text_latex += "\n" \
                          + r"\pstart" + "\n" \
                          + p.text + "\n" \
                          + r"\pend" + "\n"

    # Letter verso
    for div in soup.find_all("div", attrs={"type": "verso"}):
        verso_head = normalize_text(div.head, {"all"})
        text_latex += "\n" \
                      + r"\pstart" + "\n" \
                      + r"\textit{[" + verso_head.text + "]}" + "\n" \

        for p in div.find_all("p"):
            p = paragraph(p, filename=filename)
            if len(p.text.replace(" ", "")) > 0:
                text_latex += "\n" \
                              + r"\pstart" + "\n" \
                              + p.text + "\n" \
                              + r"\pend" + "\n"

    text_latex += "\n" \
                  + r"\endnumbering" + "\n\n" \
                  + r"\selectlanguage{english}" + "\n"
    # text_latex += "\n" + r"\pagebreak" + "\n\n"

    text_latex = latex_escape(text_latex)

    return text_latex


def main(xml, latex):
    file_name = xml.lstrip("/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/NEWNAMES/")
    print(file_name)
    with open(xml, "r", encoding="utf8") as f_xml:
        sp = BeautifulSoup(f_xml, "xml")

        # Normalize xml: removes tab, linebreak, double space
        sp = normalize_text(sp, {"xml"})

        # Delete <ref> tags from body and from header note type critIntro
        for item in sp.body.find_all("ref"):
            item.extract()
        for item in sp.teiHeader.find_all("note", {"type": "critIntro"}):
            for r in item.find_all("ref"):
                r.extract()

        # Delete milestone unit pagebreak
        for pb in sp.body.find_all("milestone", {"unit": "pb"}):
            pb.extract()

        # Remove <persName> if it contains <add> or <del> tags.
        for pers in sp.body.find_all("persName"):
            for nested in pers.find_all():
                try:
                    if nested.name == "add" or nested.name == "del":
                        pers.unwrap()
                    if nested.name == "choice":
                        print("ERROR: <choice> as child of <persName>")
                except ValueError:
                    pass

        # If <quote> not under <p> => <p><quote>
        for q in sp.find_all("quote"):
            par = q.find_parent()
            if par.name == "div":
                note_q = q.next_sibling
                p_q_note = BeautifulSoup("<p>" + str(q) + str(note_q) + "</p>", "xml")
                q.replace_with(p_q_note)
                note_q.extract()

        # Check if note type translation has p child
        # TODO

        with open("latex2_sz_2023_02_10.tex", "a", encoding="utf8") as f_latex:
            with open("xml_latex_log.tsv", "a", encoding="utf8") as f_log:
                # Write header
                h = header2latex(sp.teiHeader)
                f_latex.write(h[0])
                title_num = h[1]

                # Write text
                t = text2latex(sp.find("text"), letternum=title_num, filename=file_name)
                f_latex.write(t)

                # Write log
                xml_tup = count_xml_body(xml)
                latex_tup = count_latex_body(t)
                num_set = set()
                for i in range(7):
                    num_set.add(latex_tup[i] - xml_tup[i])
                if len(num_set) == 1 and 0 in num_set:
                    pass
                else:
                    print(f"{file_name}\t{latex_tup[0]-xml_tup[0]}\t{latex_tup[1]-xml_tup[1]}\t"
                          f"{latex_tup[2]-xml_tup[2]}\t{latex_tup[3]-xml_tup[3]}\t{latex_tup[4]-xml_tup[4]}"
                          f"\t{latex_tup[5]-xml_tup[5]}\t{latex_tup[6]-xml_tup[6]}",
                          file=f_log)


if __name__ == '__main__':
    with open("xml_latex_log.tsv", "w", encoding="utf8") as f:
        print("filename", "\t", "num_note_critic", "\t", "num_add_insert", "\t", "num_add_corr", "\t",
              "num_del_alone", "\t", "num_choice", "\t", "num_quote", "\t", "num_seg", file=f)
    with open("latex2_sz_2023_02_10.tex", "w", encoding="utf8") as f_w:
        with open("begin.txt", "r", encoding="utf8") as f_r:
            start = f_r.read()
            f_w.write(start)
    dir_name_in = "/home/eltedh/PycharmProjects/TEI2LaTeX/Olahus/XML2/"
    dir_name_out = "Olahus/LaTeX"
    f_list = file_list(dir_name_in)
    begin = time.time()
    # for i in f_list:
    #     change_xml_filename(i)
    for i in f_list:
        out = i.replace(dir_name_in, dir_name_out).replace(".xml", ".tex")
        main(i, out)
    with open("latex2_sz_2023_02_10.tex", "a", encoding="utf8") as f_w:
        # End
        f_w.write(r"\end{document}")
    end = time.time()
    print(end - begin)
