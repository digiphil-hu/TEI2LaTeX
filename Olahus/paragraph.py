from Olahus.normalize import previous_word
from normalize import normalize_text


def paragraph(para):  # <gap>

    # TODO: What would happen to the <gap>s?
    # for g in para.find_all("gap"):
    #     g.string = r"<\ldots{}>"

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

    para = normalize_text(para, {"corresp"})

    # <app> tag
    # apparatus(para)

    # <del> and no <add>
    just_del(para)

    # <del><add>
    del_add(para)

    # <add type=insert>
    add_ins(para)

    # <choice> <supplied>
    for ch in para.find_all("choice"):
        ch = choice_supplied(ch)
        ch.unwrap()

    # <quot>
    for index, quote_actual in enumerate(para.find_all("quote")):
        quote_note = para.quote.next_sibling
        if str(quote_note).startswith(r'''<note type="quote"''') is False:
            print("ERROR: Missing <note> after <quote>")

        # Linegroups
        for lg in quote_actual.find_all("lg"):
            lg_new = ""
            for l in lg.find_all("l"):
                lg_new += l.text
                if l.next_sibling is not None:
                    if l.next_sibling.name == "l":
                        lg_new += r"\\{}"
            lg_new += ""
            lg.string = lg_new
            lg.unwrap()

        quote_text = quote_actual.text

        # Footnote from quote
        note_new = r"\edtext{" + quote_text \
                   + r"}{\lemma{" + q_keyword_dict[index] \
                   + r"}\Bfootnote{" + quote_note.text + "}}"
        quote_actual.string = note_new
        quote_actual.unwrap()
        quote_note.extract()

    # seg type signature
    for s in para.find_all("seg"):
        s_new = r"\begin{flushright}" \
                + s.text + \
                r"\end{flushright}"
        s.string = s_new
        s.unwrap()

    # note critic is found under: TODO: <add>, <seg>, <quote>, <supplied>.
    # Now let's run on the remaining notes: directly under <p>
    para = note_critic(para)

    # "hi" and "names" that are not processed freviously
    para = normalize_text(para, {"milestone", "hi", "names"})

    return para


def add_ins(para):
    for _ in range(2):
        for add_in in para.find_all("add", attrs={"type": "insert"}):
            if len(add_in.find_all("add")) == 0:
                a_text = add_in.text
                a_cor = add_in["corresp"]
                a_new = r"\edtext{" + a_text + r"}{\Afootnote{\textit{" + a_cor + " add.&addins&}}}"
                add_in.string = a_new
                add_in.unwrap()


def del_add(para):
    # Norma
    for del_tag in para.find_all("del"):
        if str(del_tag.next_sibling).startswith("<add"):
            del_tag_norm = normalize_text(del_tag, {"hi", "names"})
            d_cor = del_tag["corresp"]
            d_text = del_tag_norm.text
            a = del_tag.next_sibling
            a = note_critic(a)
            a_norm = normalize_text(a, {"hi", "names"})
            a_cor = a["corresp"]
            a_text = a_norm.text
            if d_cor == a_cor:
                d_new = r"\edtext{" + a_text + r"}{\Afootnote{\textit{" + a_cor + " corr. ex} " + d_text + "&deladd&}}"
            del_tag.string = d_new
            a.extract()
            del_tag.unwrap()


def just_del(para):
    # No note_critic under <del>
    for del_alone in para.find_all("del"):
        if not str(del_alone.next_sibling).startswith("<add"):
            lastword = previous_word(del_alone)
            del_alone_norm = normalize_text(del_alone, {"hi", "names"})
            d_cor = del_alone["corresp"]
            d_text = del_alone_norm.text
            d_new = r"\edtext{" + r"}{\lemma{" + lastword + r"}\Afootnote{\textit{" + d_cor + " del. ex }" \
                    + lastword + " " + d_text + " &delalone&}}"
            del_alone.string = d_new
            del_alone.unwrap()


def apparatus(para):
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


def note_critic(tag):
    for note_tag in tag.find_all("note", attrs={"type": "critic"}):
        note_tag_norm = normalize_text(note_tag, {"hi", "names"})
        note_text = "\\footnoteA{" + note_tag_norm.text + "&notecritic&}"
        note_tag.string = note_text
        note_tag.unwrap()
    return tag


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


