from bs4 import BeautifulSoup

from normalize import normalize_text
import re


def paragraph(para):
    # Quote keywords extraction
    q_keyword_dict = {}
    for index, quote_keyword in enumerate(para.find_all("quote")):
        q = normalize_text(quote_keyword, {})
        if q.find("del") is not None:
            q.find("del").extract()
        if q.find("orig") is not None:
            q.find("orig").extract()
        q_text = q.text
        q_text = q_text.rstrip().lstrip()
        q_list = q_text.split(" ")
        if len(q_list) > 2:
            firstword = q_list[0].rstrip(".,?!")
            lastword = q_list[-1].rstrip(".,?!")
            q_keyword = firstword + r"\ldots{} " + lastword
            q_keyword_dict[index] = q_keyword
        if len(q_list) <= 2:
            q_keyword = q_text.rstrip(".,")
            q_keyword_dict[index] = q_keyword

    para = normalize_text(para, {"all"})

    for note_tag in para.find_all("note", attrs={"type": "critic"}):
        note_text = "\\footnoteA{" + note_tag.text + "}"
        note_tag.string = note_text
        # print(note_text)
        note_tag.unwrap()

    for app_tag in para.find_all("app"):
        lem_text = app_tag.lem.text
        if lem_text == "" or lem_text == " ":
            lem_text = "UNKNOWN"
        rdg_text = app_tag.rdg.text
        lem_wit = app_tag.lem["wit"].split("#")[-1]
        rdg_wit = app_tag.rdg["wit"].split("#")[-1]
        if app_tag.rdg.string is None and app_tag.rdg.find_next("del") is None:
            app_tag.string = r"\edtext{" + lem_text + r"}{\Afootnote{\textit{ms. " + rdg_wit + ". om.}}}"
            # print(app_tag.string)
            app_tag.unwrap()
            continue
        if app_tag.lem.find_next("del") is not None:
            #  print("lem alatt del:", appTag.lem)
            continue
        elif app_tag.rdg.find_next("del") is not None:
            #  print("rdg alatt del:", appTag.rdg)
            continue
        else:
            app_tag.string = r"\edtext{" + lem_text + r"}{\Afootnote{\textit{ms. " + rdg_wit + ". " + rdg_text + "}}}"
            # print(appTag.string)
            app_tag.unwrap()

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
    for _ in range(2):
        for addInsert in para.find_all("add", attrs={"type": "insert"}):
            if len(addInsert.find_all("add")) == 0:
                addInsert = add_insert(addInsert)
                addInsert.unwrap()
            """else:
            addInsertChild = addInsert.add
            addInsertChild = add_insert(addInsertChild)
            addInsertChild.unwrap()
            add_insert(addInsert)
            addInsert.unwrap()"""

    # <choice> <supplied>
    for ch in para.find_all("choice"):
        ch = choice_supplied(ch)
        ch.unwrap()

    # <quot>
    for index, quote_actual in enumerate(para.find_all("quote")):
        quote_note = para.quote.next_sibling
        if str(quote_note).startswith(r'''<note type="quote"''') is False:
            print("ERROR: Missing <note> after <quote>")
        quote_text = quote_actual.text

        # Footnote from quote
        note_new = r"\edtext{" + quote_text \
                   + r"}{\lemma{" + q_keyword_dict[index] \
                   + r"}\Bfootnote{" + quote_note.text + "}}"
        quote_actual.string = note_new
        quote_actual.unwrap()
        quote_note.extract()

    return para


def del_tag(del_tag):
    # <del> not followed by <add>
    # TODO <note> or <add> under <del>?
    d_cor = del_tag["corresp"]
    d_text = del_tag.text
    lemma = previous_word(del_tag)
    d_new = r"\edtext{" + r"}{\lemma{" + lemma + r"}\Afootnote{\textit{" + d_cor + " del. ex }" \
            + lemma + " " + d_text + "}}"
    del_tag.string = d_new
    return del_tag


def del_add(del_tag):
    d_cor = del_tag["corresp"]
    d_text = del_tag.text
    a_cor = del_tag.next_sibling["corresp"]
    a_text = del_tag.next_sibling.text
    if d_cor == a_cor:
        d_new = r"\edtext{" + a_text + r"}{\Afootnote{\textit{" + a_cor + " corr. ex} " + d_text + "}}"
    del_tag.string = d_new
    return del_tag


def add_insert(add_tag):
    a_text = add_tag.text
    a_cor = add_tag["corresp"]
    a_new = r"\edtext{" + a_text + r"}{\Afootnote{\textit{" + a_cor + " add.}}}"
    add_tag.string = a_new
    return add_tag


def choice_supplied(choice):
    if choice.supplied.corr is not None and choice.supplied.corr.string is not None:
        cor_cor = choice.supplied.corr.text
        choice.supplied.corr.extract()
        cor_sup = choice.supplied.text
        choice.string = cor_sup + "<" + cor_cor + ">"
    elif choice.supplied.corr is not None and choice.supplied.corr.string is None:
        choice.string = r"<\ldots{}> "
    else:
        orig_text = choice.orig.text
        sup_text = choice.supplied.text
        ch_new = r"\edtext{" + sup_text + r"}{\Afootnote{\textit{corr. ex} " + orig_text + "}}"
        choice.supplied.extract()
        choice.string = ch_new
    return choice


def last_word(txt):  # TODO Relocate to a place where input text is not yet normalized to avoid removing elements
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
