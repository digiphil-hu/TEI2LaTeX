from Olahus.normalize import previous_word, text_shortener, hi_rend, person_place_name, milestone_p, gap
from normalize import normalize_text


def paragraph(para, filename):  # <gap>
    # TODO: What would happen to the <gap>s?

    # Quote keywords extraction
    q_keyword_dict = {}
    for index, quote_keyword in enumerate(para.find_all("quote")):
        q = normalize_text(quote_keyword, {"nothing"})
        if q.find("del") is not None:
            q.find("del").extract()
        if q.find("orig") is not None:
            q.find("orig").extract()
        q_text = q.text
        q_keyword = text_shortener(q_text)
        q_keyword_dict[index] = q_keyword

    # <add type=insert>
    # It runs only if <add type=insert> parent is <p>, <quote> or <seg>
    for add_in in para.find_all("add", attrs={"type": "insert"}):
        for add_in_nested in add_in.find_all("add", attrs={"type": "insert"}):
            add_ins(add_in_nested)
    for add_in in para.find_all("add", attrs={"type": "insert"}):
        add_par = add_in.find_parent().name
        if add_par == "p" or add_par == "quote" or add_par == "seg":
            add_ins(add_in)

    # <app> tag
    # apparatus(para)

    # <del> and no <add>
    # It runs only if <del>'s parent is <p>, <quote> or <seg>
    for del_alone in para.find_all("del"):
        if not str(del_alone.next_sibling).startswith("<add"):
            del_alone_par = del_alone.find_parent().name
            if del_alone_par == "p" or del_alone_par == "quote" or del_alone_par == "seg":
                just_del(del_alone)

    # <del><add corr>
    # It runs only if <del><add corr>'s parent is <p>, <quote> or <seg>
    for corr_tag in para.find_all("add", {"type": "corr"}):
        if corr_tag.previous_sibling.name == "del":
            corr_tag_par = corr_tag.find_parent().name
            if corr_tag_par == "p" or corr_tag_par == "quote" or corr_tag_par == "seg":
                del_add(corr_tag)
        else:
            print("ERROR: add corr without preceding del", corr_tag)

    # <choice> <supplied>
    # As del and add already processed, choice runs everywhere
    for ch in para.find_all("choice"):
        choice_supplied(ch)

    # <quote>
    for index, quote_actual in enumerate(para.find_all("quote")):
        quote_note = para.quote.next_sibling
        if str(quote_note).startswith(r'''<note type="quote"''') is False:
            print("ERROR: Missing <note> after <quote>")

        # children of quote: hi, names, gap, note
        quote_actual = gap(quote_actual)
        quote_actual = person_place_name(quote_actual)
        quote_actual = hi_rend(quote_actual)
        quote_actual = note_critic(quote_actual)

        # children of quote note: hi
        quote_note = hi_rend(quote_note)

        # Linegroups
        for lg in quote_actual.find_all("lg"):
            lg_new = ""
            for line in lg.find_all("l"):
                lg_new += line.text
                if line.next_sibling is not None:
                    if line.next_sibling.name == "l":
                        lg_new += r"\\{}"
            lg_new += ""
            lg.string = lg_new
            lg.unwrap()

        quote_text = quote_actual.text

        # Footnote from quote
        note_new = r"\edtext{" + quote_text \
                   + r"}{\lemma{" + q_keyword_dict[index] \
                   + r"}\Bfootnote{" + quote_note.text + " &quote&}}"
        quote_actual.string = note_new
        quote_actual.unwrap()
        quote_note.extract()

    # seg type signature
    for s in para.find_all("seg"):
        s_new = r"\begin{flushright}" \
                + s.text + "&seg&" + \
                r"\end{flushright}"
        s.string = s_new
        s.unwrap()

    # note critic is found under: TODO: <add>, <seg>, <quote>, <supplied>.
    # Now let's run on the remaining notes: directly under <p> or enywhere else
    para = note_critic(para)

    para = person_place_name(para)
    para = hi_rend(para)
    para = milestone_p(para)
    para = gap(para)

    return para


def add_ins(add_ins_tag):
    for choice in add_ins_tag.find_all("choice"):
        choice_supplied(choice)
    for del_tag in add_ins_tag.find_all("del"):
        just_del(del_tag)

    add_ins_tag = gap(add_ins_tag)
    add_ins_tag = person_place_name(add_ins_tag)
    add_ins_tag = hi_rend(add_ins_tag)
    add_ins_tag = note_critic(add_ins_tag)

    a_text = add_ins_tag.text
    a_cor = add_ins_tag["corresp"]
    a_new = r"\edtext{" + a_text + r"}{\Afootnote{\textit{" + a_cor + " add. &addins&}}}"
    add_ins_tag.string = a_new
    add_ins_tag.unwrap()


def del_add(add_corr):
    # Child of <del>: only <gap>
    # Child of <add corr>: names, notes, gap, <del>
    del_corr = add_corr.previous_sibling
    del_corr = gap(del_corr)
    del_corr_name = del_corr["corresp"]
    add_corr_name = add_corr["corresp"]
    short_text = text_shortener(add_corr.text)
    for del_in_add_corr in add_corr.find_all("del"):
        just_del(del_in_add_corr)
    add_corr = gap(add_corr)
    add_corr = person_place_name(add_corr)
    add_corr = hi_rend(add_corr)
    add_corr = note_critic(add_corr)
    if del_corr_name == add_corr_name:
        add_new = r"\edtext{" + add_corr.text + r"}{\lemma{" + short_text + r"}\Afootnote{\textit{" \
                  + add_corr_name + " corr. ex} " + del_corr.text + " &deladd&}}"
    else:
        print("ERROR: del and add corresp do not match")
        add_new = ""
    add_corr.string = add_new
    del_corr.extract()
    add_corr.unwrap()


def just_del(del_alone):
    # No note_critic under <del>
    lastword = previous_word(del_alone)

    del_alone = hi_rend(del_alone)
    del_alone = person_place_name(del_alone)

    d_cor = del_alone["corresp"]
    d_text = del_alone.text
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
    # The only child of note critic is <hi>
    for note in tag.find_all("note", {"type": "critic"}):
        note = hi_rend(note)
        note = person_place_name(note)
        try:
            print("ERROR: Note critic has child", note.find_child())
        except TypeError:
            pass
        note_text = r"\footnoteA{" + note.text + " &notecritic&}"
        note.string = note_text
        note.unwrap()
    return tag


def choice_supplied(choice):
    # Children of choice: hi, name, gap
    # Children of orig: hi, gap. del, add => manual correction needed!

    choice = gap(choice)
    choice = person_place_name(choice)
    choice = hi_rend(choice)
    if choice.supplied.corr is not None and choice.supplied.corr.string is not None:
        cor_cor = choice.supplied.corr.text
        choice.supplied.corr.extract()
        cor_sup = choice.supplied.text
        choice.string = cor_sup + "<" + cor_cor + "> &choice&"
        # print(choice.string)
    elif choice.supplied.corr is not None and choice.supplied.corr.text.replace(" ", "") == "":
        choice.string = r"<\ldots{}> &choice&"
    else:
        orig_text = choice.orig.text
        sup_text = choice.supplied.text
        ch_new = r"\edtext{" + sup_text + r"}{\Afootnote{\textit{corr. ex} " + orig_text + " &choice&}}"
        choice.string = ch_new
    # print(choice.string)
    choice.unwrap()


