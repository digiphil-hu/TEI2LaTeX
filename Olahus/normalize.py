import re
from bs4 import BeautifulSoup


def normalize_text(soup, what_to_do):
    soup_str = str(soup)

    if "xml" in what_to_do:
        soup_str = re.sub(r"[\n\t]+", "", soup_str)
        soup_str = re.sub(r"\s+", " ", soup_str)

    if "all" in what_to_do:
        # soup_str = soup_str.replace("[", "{[}")
        # soup_str = soup_str.replace("]", "{]}")
        # soup_str = soup_str.replace("-", r"\-")
        soup_str = milestone_p(soup_str)
        soup_str = corresp_changes(soup_str)
        soup_str = hi_rend(soup_str)
        soup_str = person_place_name(soup_str)

    if "header" in what_to_do:
        soup_str = soup_str.replace("[", "{[}")
        soup_str = soup_str.replace("]", "{]}")
        soup_str = soup_str.replace("(", "{(}")
        soup_str = soup_str.replace(")", "{)}")
        soup_str = soup_str.replace("-", r"\-")
        soup_str = hi_rend(soup_str)

    else:
        if "milestone" in what_to_do:
            soup_str = milestone_p(soup_str)
        if "corresp" in what_to_do:
            soup_str = corresp_changes(soup_str)
        if "hi" in what_to_do:
            soup_str = hi_rend(soup_str)
        if "names" in what_to_do:
            soup_str = person_place_name(soup_str)

    soup = BeautifulSoup(soup_str, "xml")
    return soup


def milestone_p(string):
    string = re.sub("<milestone unit=\"p\"/>", "{[}BEKEZDÉSHATÁR{]}", string)
    string = string.replace(r"{[}BEKEZDÉSHATÁR{]}", "\n\\pend\n\n\\pstart\n")
    return string


def corresp_changes(string): # <del corresp="editor">
    string = re.sub("corresp=\"Olahus\"", "corresp=\"O\"", string)
    string = re.sub("corresp=\"editor\"", "corresp=\" \"", string)
    string = re.sub("corresp=\"scriba\"", "corresp=\"scr\"", string)
    return string


def latex_escape(string):
    string = string.replace("_", r"\_")
    string = string.replace("-", r"\-")
    string = string.replace("#", r"\#")
    string = string.replace("%", r"\%")
    string = string.replace("[", "{[}")
    string = string.replace("]", "{]}")

    # Replace false escapea
    string = string.replace("edindex{[}place{]}", "edindex[place]")
    string = string.replace("edindex{[}pers{]}", "edindex[pers]")
    string = string.replace("{\-1", "{-1")
    string = string.replace("\Xtxtbeforenumber{[}A{]}", "\Xtxtbeforenumber[A]")
    string = string.replace("\Xtxtbeforenumber{[}B{]}", "\Xtxtbeforenumber[B]")

    return string


def hi_rend(string):
    # hi rend. As italic, super and small-cap may be under bold or italic, two cycles are needed.
    soup = BeautifulSoup(string, "xml")
    for hi in soup.find_all("hi"):
        if len(hi.find_all("hi")) == 0:  # If there are no <hi> under <hi>
            hi_text = hi.text
            if hi["rend"] == "italic":
                hi.string = r"\textit{" + hi_text + "}"
                hi.unwrap()
            elif hi["rend"] == "smallcap":
                hi.string = r"\textsc{" + hi_text + "}"
                hi.unwrap()
            elif hi["rend"] == "super":
                hi.string = r"\textsuperscript{" + hi_text + "}"
                hi.unwrap()
            elif hi["rend"] == "bold":
                hi.string = r"\textbf{" + hi_text + "}"
                hi.unwrap()
            elif hi["rend"] == "expanded":
                hi.string = r"\textbf{" + hi_text + "}"
                hi.unwrap()
            else:
                print("<hi> error:", hi)

    # Upper <hi>
    for hi in soup.find_all("hi"):
        hi_text = hi.text
        if len(hi.find_all("hi")) == 0:
            if hi["rend"] == "bold":
                hi.string = r"\textbf{" + hi_text + "}"
            elif hi["rend"] == "italic":
                hi.string = r"\textit{" + hi_text + "}"
            elif hi["rend"] == "expanded":
                hi.string = r"\textbf{" + hi_text + "}"
            else:
                print("<hi><hi> error:", hi)
            hi.unwrap()

    return str(soup)


def person_place_name(string):
    soup = BeautifulSoup(string, "xml")
    for name in soup.find_all("persName"):
        name.string = "\edindex[pers]{" + name.text + "}" + name.text
        name.unwrap()
    for place in soup.find_all("placeName"):
        place.string = "\edindex[place]{" + place.text + "}" + place.text
        place.unwrap()
    return str(soup)


def previous_word(del_a):
    taglist = ["persName", "placeName", "add"]
    if del_a.previous_element.name is None:
        if del_a.previous_element.text.replace(" ", "") == "":
            try:
                prev_prev = del_a.find_previous_sibling()
                if prev_prev.name in taglist:
                    raw_text = prev_prev.text
                    # print("Name, Add", raw_text)
                if prev_prev.name == "choice":
                    raw_text = prev_prev.supplied.text
                    # print("Choice", raw_text)
                if prev_prev.name == "note":
                    raw_text = prev_prev.previous_element.text
                    # print("note", raw_text)
            except AttributeError:
                raw_text = "VEZÉRSZÓ"
                # print("NINCS előző tag!")
        else:
            raw_text = del_a.previous_element.text
            # print("Szöveg, tele.", raw_text)
    else:
        if del_a.previous_element.name == "add":
            raw_text = del_a.previous_element.text
            # print("Add", raw_text)
        if del_a.previous_element.name == "milestone":
            prev_elem = del_a.previous_element
            raw_text = prev_elem.previous_element.text
            # print("Milestone", raw_text)
        if del_a.previous_element.name == "p":
            raw_text = "VEZÉRSZÓ"
            # print("p", raw_text)

    raw_text = re.sub("[\d,\.();!?:\[\]†]+", "", raw_text)
    txt_list = raw_text.rstrip().split(" ")
    lastword = txt_list[-1]
    if lastword != "":
        return lastword
    else:
        return "VEZÉRSZÓ"
