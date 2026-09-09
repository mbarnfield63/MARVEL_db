# Browser-sweep results. rank -> (data_status, [(url, link_kind), ...], note)
OUP = "https://academic.oup.com"
AIP = "https://pubs.aip.org"
CLD = "https://content.cld.iop.org/journals"


def mrt(base, art, ns, tar=None):
    out = [(f"https://iopscience.iop.org/{base}/suppdata/{art}t{n}_ascii.txt", "journal_table") for n in ns]
    if tar:
        out.append((tar, "SI_zip"))
    return out


SWEEP = {
 # --- Oxford University Press: article page + #supplementary-data (asset URLs are tokenised) ---
 3:  ("levels+trans", [(OUP + "/mnras/article/doi/10.1093/mnras/stag979/8691585#supplementary-data", "SI_zip")],
      "SI stag979_Supplemental_Files.zip = Duo input + MARVEL input/output/segment files for 39KH"),
 30: ("levels+trans", [(OUP + "/rasti/article/3/1/565/7746432#supplementary-data", "SI_zip")],
      "SI rzae037_Supplemental_Files.zip = MARVEL energy, transitions and segment files for 24Mg16O, 48Ti16O, 51V16O"),
 32: ("levels+trans", [(OUP + "/mnras/article/531/3/3023/7684295#supplementary-data", "SI_zip")],
      "SI stae1340_Supplemental_File.zip; contents not itemised on the article page - verify on download"),
 33: ("levels+trans", [(OUP + "/mnras/article/536/1/714/7906605#supplementary-data", "SI_zip")],
      "SI stae2610_Supplemental_File.zip = Duo input + MARVEL input (transitions and segment) and output (energy) files + PGOPHER file"),
 43: ("levels+trans", [(OUP + "/mnras/article/533/3/3442/7725073#supplementary-data", "SI_zip")],
      "SI stae1849_Supplemental_File.zip = MARVEL input (transitions and segment) and output (energy) files + HITRAN-format 15NH3 lines"),
 45: ("levels+trans", [(OUP + "/mnras/article/527/3/6675/7424995#supplementary-data", "SI_zip")],
      "SI stad3508_Supplemental_File.zip = Duo input carrying MARVEL term values + the MARVEL data set"),
 54: ("levels+trans", [(OUP + "/mnras/article/527/4/9736/7468140#supplementary-data", "SI_zip")],
      "SI stad3802_Supplemental_Files.zip = Duo input + MARVEL input and output files"),
 55: ("levels+trans", [(OUP + "/mnras/article/527/3/4899/7326798#supplementary-data", "SI_zip")],
      "SI stad3225_Supplemental_File.zip = Duo input with experimental YO term values + line positions in MARVEL format"),
 60: ("levels+trans", [(OUP + "/mnras/article/511/4/5448/6526890#supplementary-data", "SI_zip")],
      "SI stac371_Supplemental_File.zip; contents not itemised on the article page - verify on download"),
 63: ("levels+trans", [(OUP + "/mnras/article/516/1/1158/6649334#supplementary-data", "SI_zip")],
      "SI stac2004_Supplemental_Files.zip = MARVEL input transitions and output energy files + PGOPHER + partition function"),
 64: ("levels+trans", [(OUP + "/mnras/article/520/4/5183/6958824#supplementary-data", "SI_zip")],
      "SI stac3757_Supplemental_Files.zip; caption mentions only partition functions - MARVEL content unverified"),
 66: ("levels+trans", [(OUP + "/mnras/article/508/3/3181/6368347#supplementary-data", "SI_zip")],
      "SI stab2525_Supplemental_File.zip; abstract reports 22473 validated transitions giving 6485 levels"),
 71: ("levels+trans", [(OUP + "/mnras/article/505/3/4383/6288427#supplementary-data", "SI_zip")],
      "SI stab1551_Supplementary_File.zip = updated MARVEL files"),
 73: ("levels+trans", [(OUP + "/mnras/article/510/1/903/6426188#supplementary-data", "SI_zip")],
      "SI stab3267_Supplemental_File.zip = MARVEL input transitions and output energy levels + Duo input"),
 80: ("levels+trans", [(OUP + "/mnras/article/497/1/1081/5870682#supplementary-data", "SI_zip")],
      "SI staa1954_Supplemental_Files.zip = 12C-12C_2020update.marvel.inp, energies, line lists"),
 81: ("levels+trans", [(OUP + "/mnras/article/499/1/25/5904777#supplementary-data", "SI_zip")],
      "SI staa2791_Supplemental_Files.zip = full MARVEL input file + vibronic-resolution tables"),
 91: ("levels+trans", [(OUP + "/mnras/article/486/2/2351/5475901#supplementary-data", "SI_zip")],
      "SI 'Supplemental File.zip' = MARVEL transitions and energy files + Duo input"),
 101: ("levels+trans", [(OUP + "/mnras/article/479/1/1401/5035837#supplementary-data", "SI_zip")],
      "SI 'Supplement Files.zip'; contents not itemised on the article page - verify on download"),
 110: ("levels+trans", [(OUP + "/mnras/article/470/1/882/3833248#supplementary-data", "SI_zip")],
      "SI sl.zip; contents not itemised on the article page - verify on download"),

 # --- AIP ---
 15: ("levels+trans", [(AIP + "/jpr/article/54/2/023103/3350611", "SI_zip")],
      "SI = complete line list of the analysed FTS spectra + derived HD17O and HD18O energy level sets"),
 67: ("levels+trans", [(AIP + "/jcp/article/154/7/074112/200853", "SI_zip")],
      "SI zip = three text files including the Duo input and the NO transition data"),
 77: ("levels+trans", [(AIP + "/jpr/article/49/3/033101/242136", "SI_zip")],
      "SI zip = W2020 H216O validated transitions and empirical energy levels"),
 78: ("levels+trans", [(AIP + "/jpr/article/49/4/043103/242144", "SI_zip")],
      "SI zip = transitions and energy levels for W2020 H216O, H217O and H218O"),
 89: ("levels+trans", [(AIP + "/jpr/article/48/2/023101/242060", "SI_zip")],
      "SI zip = 16O2 MARVEL transitions and empirical rovibronic energy levels"),

 # --- Wiley ---
 22: ("levels+trans", [("https://onlinelibrary.wiley.com/doi/10.1002/jcc.27453", "SI_zip")],
      "SI jcc27453-sup-0001-Supinfo.zip"),
 24: ("levels+trans", [("https://onlinelibrary.wiley.com/doi/10.1002/jcc.27541", "SI_zip")],
      "SI jcc27541-sup-0001-Supinfo.zip"),
 27: ("levels+trans", [("https://onlinelibrary.wiley.com/doi/10.1002/jcc.27266", "SI_zip")],
      "SI jcc27266-sup-0001-supinfo.zip"),

 # --- Taylor & Francis ---
 14: ("levels+trans", [("https://doi.org/10.6084/m9.figshare.30051165", "repository"),
                      ("https://www.tandfonline.com/doi/suppl/10.1080/00268976.2025.2550568", "SI_zip")],
      "figshare mirror of the T&F supplemental zip (305.7 kB)"),
 52: ("levels+trans", [("https://www.tandfonline.com/doi/full/10.1080/00268976.2023.2276912", "SI_file")],
      "data availability: MARVEL input transitions file, MARVEL output energy file and segment file; T&F asset URLs are tokenised"),
 53: ("levels+trans", [("https://www.tandfonline.com/doi/full/10.1080/00268976.2023.2279694", "SI_file")],
      "data availability: MARVEL input transitions file, MARVEL output energy file and segment file; T&F asset URLs are tokenised"),

 # --- Elsevier: SI referenced in the paper but no asset exposed anywhere ---
 57: ("unreachable", [("https://www.sciencedirect.com/science/article/pii/S0022407322002308", "landing_page")],
      "data availability states the MARVEL transitions and energy files are supplementary, but no SI asset is exposed and the mmc probe found none - manual chase"),

 # --- IOP / AAS machine-readable tables ---
 2:  ("levels+trans", mrt("0067-0049/283/1/39", "apjsae40f0", range(1, 8)),
      "MARVEL input transitions and output energies as AAS machine-readable tables, 5 CO isotopologues"),
 13: ("levels+trans", mrt("0067-0049/276/2/66", "apjsada3c9", range(1, 6)),
      "Appendix 'MARVEL Files': input transitions, segment file and output energies as machine-readable tables"),
 86: ("levels+trans", mrt("0067-0049/248/1/9", "apjsab85cb", range(1, 5),
      CLD + "/0067-0049/248/1/9/revision1/apjsab85cb_table4.tar.gz"),
      "MARVEL input and output files for CaOH"),
 96: ("levels+trans", mrt("0004-637X/867/1/33", "apjaadd19", range(1, 4)),
      "90Zr-16O data compiled to MARVEL format, given as machine-readable tables"),
 105: ("levels+trans", mrt("0067-0049/228/2/15", "apjsaa5930", [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14],
       CLD + "/0067-0049/228/2/15/revision1/apjsaa5930_table2.tar.gz"),
       "SI files 48Ti-16O.marvel.inp, 48Ti-16O.energies, 48Ti-16O_FFN_ca33.energies"),
 113: ("levels+trans", mrt("0067-0049/224/2/44", "apjsaa2378", range(1, 9),
       CLD + "/0067-0049/224/2/44/revision1/apjsaa2378.tar.gz"),
       "MARVEL input transitions file and output energies file"),
 5:  ("levels+trans", [(CLD + "/0741-3335/68/6/065043/revision2/ppcfae72ccsupp2.txt", "SI_file"),
                      (CLD + "/0741-3335/68/6/065043/revision2/ppcfae72ccsupp3.txt", "SI_file")],
      "two supplementary text files, listed at iopscience.iop.org/article/10.1088/1361-6587/ae72cc/data"),

 # --- Royal Society of Chemistry ---
 46: ("levels+trans", [(f"https://pubs.rsc.org/cp/article-supplement/801363/txt/d3cp01835k{n}_suppl/", "SI_file")
                      for n in range(1, 4)],
      "three SI text files"),
 58: ("levels+trans", [(f"https://pubs.rsc.org/cp/article-supplement/761512/txt/d2cp02240k{n}_suppl/", "SI_file")
                      for n in range(1, 9)],
      "eight SI text files covering 12CH and 16OH"),
 92: ("companion", [("https://pubs.rsc.org/cp/article/21/7/3473/599379", "landing_page")],
      "no ESI listed by RSC for this article; the W2018 H216O dataset is superseded by W2020 (see 20FuToTea/b) and the W2024 OSF repository"),
 125: ("levels+trans", [("https://pubs.rsc.org/cp/article-supplement/395686/txt/c3cp44610g_suppl/", "SI_file"),
                       ("https://pubs.rsc.org/cp/article-supplement/395686/txt/c3cp44610g_2_suppl/", "SI_file"),
                       ("https://pubs.rsc.org/cp/article-supplement/395686/zip/c3cp44610g_suppl/", "SI_zip")],
       "SI files Transitions_h2d.txt, Transitions_d2h.txt, EnergyComparison.zip"),

 # --- ACS ---
 124: ("levels+trans", [(f"https://pubs.acs.org/jctcce/article-supplement/846952/txt/ct4004355_si_{n:03d}/", "SI_file")
                       for n in range(1, 9)],
       "eight SI text files"),
}
