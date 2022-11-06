import re
from bs4 import BeautifulSoup


def normalize_text(soup, what_to_do):
    soup_str = str(soup)
    soup_str = re.sub("[\n\t\s]+", " ", soup_str)
    soup_str = re.sub("\s+", " ", soup_str)
    soup_str = re.sub("\[\d+.", "{[}", soup_str)
    soup_str = re.sub("\d.\]", "{]}", soup_str)
    soup_str = re.sub("_", "\\_", soup_str)
    soup_str = re.sub("#", "\\#", soup_str)

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
        if "escape" in what_to_do:
            soup_str = latex_escape(soup_str)
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
    string = re.sub("\[", "{[}", string)
    string = re.sub("\]", "{]}", string)
    string = re.sub("_", "\\_", string)
    string = re.sub("#", "\\#", string)
    return string


def hi_rend(string):
    # hi rend. As italic, super and small-cap may be under bold or italic, two cycles are needed.
    soup = BeautifulSoup(string, "xml")
    for hi in soup.find_all("hi"):
        if len(hi.find_all("hi")) == 0:  # If there are no <hi> under <hi>
            hi_text = hi.text
            if hi["rend"] == "italic":
                hi.string = "\\textit{" + hi_text + "}"
                hi.unwrap()
            elif hi["rend"] == "smallcap":
                hi.string = "\\textsc{" + hi_text + "}"
                hi.unwrap()
            elif hi["rend"] == "super":
                hi.string = "^" + hi_text # HIBA, csak egy betűt emel fel!
                hi.unwrap()
            elif hi["rend"] == "bold":
                hi.string = "\\textbf{" + hi_text + "}"
                hi.unwrap()
            else:
                print("<hi> error:", hi)

    # Upper <hi>
    for hi in soup.find_all("hi"):
        hi_text = hi.text
        if len(hi.find_all("hi")) == 0:
            if hi["rend"] == "bold":
                hi.string = "\\textbf{" + hi_text + "}"
            elif hi["rend"] == "italic":
                hi.string = "\\textit{" + hi_text + "}"
            else:
                print("<hi><hi> error:", hi)
            hi.unwrap()

    return str(soup)


def person_place_name(string):
    soup = BeautifulSoup(string, "xml")
    for name in soup.find_all("persName"):
        name.string = "\index[pers]{" + name.text + "}" + name.text
        name.unwrap()
    for place in soup.find_all("placeName"):
        place.string = "\index[place]{" + place.text + "}" + place.text
        place.unwrap()
    return str(soup)