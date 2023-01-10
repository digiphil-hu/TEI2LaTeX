import re
from bs4 import BeautifulSoup


def normalize_text(soup, what_to_do):  # re.sub helyett replace
    soup_str = str(soup)
    soup_str = re.sub("[\n\t\s]+", " ", soup_str)
    soup_str = re.sub("\s+", " ", soup_str)
    soup_str = soup_str.replace("[", "{[}")
    soup_str = soup_str.replace("]", "{]}")
    soup_str = soup_str.replace("-", r"\-")

    if "all" in what_to_do:
        soup_str = milestone_p(soup_str)
        soup_str = corresp_changes(soup_str)
        soup_str = hi_rend(soup_str)
        soup_str = person_place_name(soup_str)
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
    return string


def corresp_changes(string):
    string = re.sub("corresp=\"Olahus\"", "corresp=\"O.\"", string)
    string = re.sub("corresp=\"editor\"", "corresp=\" \"", string)  # <del corresp="editor">
    return string


def latex_escape(string):
    string = string.replace("_", r"\_")
    string = string.replace("#", r"\#")
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
