"""Styles SLD 1.0 des couches publiées, dans la palette de la carte web (DESIGN.md) : encre sépia sur
papier, carmin pour le transport HTB, bleu de Prusse pour la distribution, vert pour l'environnement.
Les titres des règles sont les libellés de la légende MapStore. Les seuils d'échelle reprennent ceux de
la carte web (pylônes au 1:46 000, postes HTA/BT au 1:33 000, BT au 1:23 000, poteaux au 1:8 200).
"""
from xml.sax.saxutils import escape

ENCRE, ENCRE_2, ENCRE_3 = "#2f241d", "#5a4a3d", "#6f5f51"
PAPIER, FILET = "#faf8f3", "#d8d1c4"
CARMIN, BLEU, VERT, VERT_FONCE, SEPIA = "#c8385a", "#4f7fb0", "#8fae74", "#5d7d47", "#9a8470"
POLICE = "Segoe UI"  # police installée dans le GeoServer de la pile


# ---------------------------------------------------------------- Briques
def css(nom, valeur):
    return f'<CssParameter name="{nom}">{valeur}</CssParameter>'


def trait(couleur, largeur, opacite=1.0, tirets=None, bout="butt"):
    p = css("stroke", couleur) + css("stroke-width", largeur) + css("stroke-linejoin", "round") + css("stroke-linecap", bout)
    if opacite < 1:
        p += css("stroke-opacity", opacite)
    if tirets:
        p += css("stroke-dasharray", tirets)
    return f"<Stroke>{p}</Stroke>"


def plein(couleur, opacite=1.0):
    return f"<Fill>{css('fill', couleur)}{css('fill-opacity', opacite) if opacite < 1 else ''}</Fill>"


def hachure(couleur, motif="slash", ecart=9, largeur=1.0):
    return (f"<Fill><GraphicFill><Graphic><Mark><WellKnownName>shape://{motif}</WellKnownName>"
            f"{trait(couleur, largeur)}</Mark><Size>{ecart}</Size></Graphic></GraphicFill></Fill>")


def polygone(fond=None, opacite=1.0, contour=None, largeur=1.0, tirets=None, motif=None):
    remplissage = motif or (plein(fond, opacite) if fond else "")
    bord = trait(contour, largeur, 1.0, tirets) if contour else ""
    return f"<PolygonSymbolizer>{remplissage}{bord}</PolygonSymbolizer>"


def ligne(couleur, largeur, opacite=1.0, tirets=None, bout="butt"):
    return f"<LineSymbolizer>{trait(couleur, largeur, opacite, tirets, bout)}</LineSymbolizer>"


def marque(forme, taille, fond, contour=None, largeur=1.0, rotation=0, opacite=1.0):
    rot = f"<Rotation>{rotation}</Rotation>" if rotation else ""
    return (f"<PointSymbolizer><Graphic><Mark><WellKnownName>{forme}</WellKnownName>"
            f"{plein(fond, opacite)}{trait(contour, largeur) if contour else ''}</Mark>"
            f"<Size>{taille}</Size>{rot}</Graphic></PointSymbolizer>")


def texte(champ, taille, couleur=ENCRE, style="normal", poids="normal", ancre=(0.5, 0.5), decalage=(0, 0),
          halo=PAPIER, cadre=False, geom=None, suivre_ligne=False):
    police = css("font-family", POLICE) + css("font-size", taille) + css("font-style", style) + css("font-weight", poids)
    g = f"<Geometry><ogc:PropertyName>{geom}</ogc:PropertyName></Geometry>" if geom else ""
    if suivre_ligne:
        placement = "<LabelPlacement><LinePlacement/></LabelPlacement>"
    else:
        placement = (f"<LabelPlacement><PointPlacement><AnchorPoint><AnchorPointX>{ancre[0]}</AnchorPointX>"
                     f"<AnchorPointY>{ancre[1]}</AnchorPointY></AnchorPoint><Displacement>"
                     f"<DisplacementX>{decalage[0]}</DisplacementX><DisplacementY>{decalage[1]}</DisplacementY>"
                     f"</Displacement></PointPlacement></LabelPlacement>")
    h = f"<Halo><Radius>1.5</Radius>{plein(halo)}</Halo>" if halo and not cadre else ""
    # Étiquette encadrée (filet d'encre sur papier), comme les cartouches de la carte web
    fond = (f"<Graphic><Mark><WellKnownName>square</WellKnownName>{plein(PAPIER)}{trait(ENCRE, 1)}</Mark></Graphic>"
            '<VendorOption name="graphic-resize">stretch</VendorOption>'
            '<VendorOption name="graphic-margin">2 5 2 5</VendorOption>') if cadre else ""
    return (f"<TextSymbolizer>{g}<Label><ogc:PropertyName>{champ}</ogc:PropertyName></Label>"
            f"<Font>{police}</Font>{placement}{h}{plein(couleur)}{fond}"
            '<VendorOption name="conflictResolution">true</VendorOption>'
            '<VendorOption name="partials">false</VendorOption></TextSymbolizer>')


def egal(champ, valeur):
    return (f"<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>{champ}</ogc:PropertyName>"
            f"<ogc:Literal>{escape(str(valeur))}</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>")


def entre(champ, mini=None, maxi=None):
    conditions = []
    if mini is not None:
        conditions.append(f"<ogc:PropertyIsGreaterThanOrEqualTo><ogc:PropertyName>{champ}</ogc:PropertyName>"
                          f"<ogc:Literal>{mini}</ogc:Literal></ogc:PropertyIsGreaterThanOrEqualTo>")
    if maxi is not None:
        conditions.append(f"<ogc:PropertyIsLessThan><ogc:PropertyName>{champ}</ogc:PropertyName>"
                          f"<ogc:Literal>{maxi}</ogc:Literal></ogc:PropertyIsLessThan>")
    corps = conditions[0] if len(conditions) == 1 else f"<ogc:And>{''.join(conditions)}</ogc:And>"
    return f"<ogc:Filter>{corps}</ogc:Filter>"


def regle(titre, *symboles, filtre="", echelle_max=None, echelle_min=None):
    e = (f"<MinScaleDenominator>{echelle_min}</MinScaleDenominator>" if echelle_min else "") + \
        (f"<MaxScaleDenominator>{echelle_max}</MaxScaleDenominator>" if echelle_max else "")
    t = f"<Title>{escape(titre)}</Title>" if titre else ""
    # une règle sans titre (étiquettes) est dessinée mais n'entre pas dans la légende
    hors_legende = "" if titre else '<VendorOption name="inclusion">mapOnly</VendorOption>'
    return f"<Rule><Name>{escape(titre or 'etiquettes')}</Name>{t}{filtre}{e}{''.join(symboles)}{hors_legende}</Rule>"


def sld(nom, *regles):
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" '
            'xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">'
            f"<NamedLayer><Name>{nom}</Name><UserStyle><Name>{nom}</Name><FeatureTypeStyle>"
            f"{''.join(regles)}</FeatureTypeStyle></UserStyle></NamedLayer></StyledLayerDescriptor>")


# ---------------------------------------------------------------- Styles
def styles():
    s = {}
    s["penly_cnpe"] = sld("penly_cnpe", regle(
        "CNPE de Penly",
        marque("circle", 20, PAPIER, ENCRE, 1.6), marque("circle", 9, CARMIN),
        texte("nom", 14, ENCRE, "italic", "bold", ancre=(0, 0.5), decalage=(16, 0))))
    s["penly_cercles"] = sld("penly_cercles", regle(
        "Cercles de 2, 5, 10 et 20 km autour du CNPE",
        polygone(contour=ENCRE, largeur=1.2, tirets="8 5"),
        texte("etiquette", 12, ENCRE, poids="600", geom="geom_etiquette", cadre=True)))
    s["penly_htb_lignes"] = sld(
        "penly_htb_lignes",
        regle("Ligne 400 kV", ligne(PAPIER, 8, 0.85, bout="round"), ligne(CARMIN, 4.2, bout="round"),
              filtre=entre("tension_kv", 300)),
        regle("Ligne 90 kV", ligne(PAPIER, 5.5, 0.85, bout="round"), ligne(CARMIN, 2.4, bout="round"),
              filtre=entre("tension_kv", None, 300)))
    s["penly_htb_postes"] = sld("penly_htb_postes", regle(
        "Poste électrique HTB", polygone(CARMIN, 0.28, CARMIN, 1.4)))
    s["penly_htb_pylones"] = sld("penly_htb_pylones", regle(
        "Pylône", marque("square", 6, PAPIER, CARMIN, 1.2), echelle_max=46000))
    s["penly_hta"] = sld(
        "penly_hta",
        regle("HTA aérienne", ligne(BLEU, 1.6), filtre=egal("pose", "aérienne")),
        regle("HTA souterraine", ligne(BLEU, 1.5, tirets="5 3"), filtre=egal("pose", "souterraine")))
    s["penly_bt"] = sld(
        "penly_bt",
        regle("BT aérienne", ligne(BLEU, 0.9, 0.75), filtre=egal("pose", "aérienne"), echelle_max=23000),
        regle("BT souterraine", ligne(BLEU, 0.9, 0.75, tirets="2 2"), filtre=egal("pose", "souterraine"),
              echelle_max=23000))
    s["penly_postes_hta_bt"] = sld("penly_postes_hta_bt", regle(
        "Poste HTA/BT", marque("triangle", 9, PAPIER, BLEU, 1.4), echelle_max=33000))
    s["penly_poteaux"] = sld("penly_poteaux", regle(
        "Poteau HTA ou BT", marque("circle", 4, BLEU, PAPIER, 0.6), echelle_max=8200))
    s["penly_production"] = sld(
        "penly_production",
        *(regle(titre, marque("circle", taille, PAPIER, ENCRE, 1.3, opacite=0.6), filtre=entre("puissance_kw", a, b))
          for titre, taille, a, b in [("moins de 100 kW", 7, None, 100), ("100 kW à 1 MW", 10, 100, 1000),
                                      ("1 à 10 MW", 14, 1000, 10000), ("10 à 100 MW", 19, 10000, 100000),
                                      ("plus de 100 MW (CNPE compris)", 28, 100000, None)]))
    douteuse = ("<ogc:Filter><ogc:PropertyIsEqualTo><ogc:PropertyName>position_douteuse</ogc:PropertyName>"
                "<ogc:Literal>true</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>")
    s["penly_icpe"] = sld(
        "penly_icpe",
        regle("Autorisation", marque("square", 9, ENCRE, PAPIER, 0.8, rotation=45), filtre=egal("regime", "A")),
        regle("Enregistrement", marque("square", 9, PAPIER, ENCRE, 1.4, rotation=45), filtre=egal("regime", "E")),
        regle("Autre régime ou non classé", marque("circle", 5, ENCRE_3, PAPIER, 0.6),
              filtre="<ogc:Filter><ogc:Not><ogc:Or>"
                     "<ogc:PropertyIsEqualTo><ogc:PropertyName>regime</ogc:PropertyName><ogc:Literal>A</ogc:Literal></ogc:PropertyIsEqualTo>"
                     "<ogc:PropertyIsEqualTo><ogc:PropertyName>regime</ogc:PropertyName><ogc:Literal>E</ogc:Literal></ogc:PropertyIsEqualTo>"
                     "</ogc:Or></ogc:Not></ogc:Filter>"),
        regle("Position douteuse",  # titre court : une légende large est réduite dans la table des matières
              "<PointSymbolizer><Graphic><Mark><WellKnownName>circle</WellKnownName>"
              f"{trait(CARMIN, 1.8)}</Mark><Size>17</Size></Graphic></PointSymbolizer>", filtre=douteuse))
    s["penly_znieff1"] = sld("penly_znieff1", regle("ZNIEFF de type I", polygone(VERT, 0.25, VERT_FONCE, 1)))
    s["penly_znieff2"] = sld("penly_znieff2", regle("ZNIEFF de type II", polygone(VERT, 0.08, VERT, 1.2, tirets="7 4")))
    s["penly_natura2000_zsc"] = sld("penly_natura2000_zsc", regle(
        "Natura 2000, directive Habitats (ZSC)", polygone(contour=VERT_FONCE, largeur=1.3, motif=hachure(VERT_FONCE, "slash"))))
    s["penly_natura2000_zps"] = sld("penly_natura2000_zps", regle(
        "Natura 2000, directive Oiseaux (ZPS)",
        polygone(contour=VERT_FONCE, largeur=1.3, tirets="9 4", motif=hachure(VERT_FONCE, "backslash", 12, 0.8))))
    s["penly_conservatoire"] = sld("penly_conservatoire", regle(
        "Conservatoire du littoral", polygone(SEPIA, 0.32, SEPIA, 1.1)))
    s["penly_communes"] = sld(
        "penly_communes",
        regle("Limite communale", polygone(contour=ENCRE_3, largeur=0.8, tirets="4 3")),
        regle("", texte("nom", 12, ENCRE_2, "italic"), echelle_max=150000))
    s["penly_batiments"] = sld("penly_batiments", regle(
        "Bâtiment", polygone(FILET, 1, "#b9ae9d", 0.5), echelle_max=20000))
    s["penly_parcelles"] = sld(
        "penly_parcelles",
        regle("Parcelle cadastrale", polygone(contour=SEPIA, largeur=0.6), echelle_max=12000),
        regle("", texte("numero", 9, ENCRE_3, halo=PAPIER), echelle_max=3500))
    return s
